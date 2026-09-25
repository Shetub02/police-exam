-- Run once in Supabase SQL Editor. Each account can read only its own progress.
create table if not exists public.police_progress (
  user_id uuid primary key references auth.users(id) on delete cascade,
  revision bigint not null default 1,
  payload jsonb not null,
  updated_at timestamptz not null default now(),
  check (octet_length(payload::text) <= 2000000)
);
alter table public.police_progress enable row level security;
revoke all on public.police_progress from anon, authenticated;
grant select on public.police_progress to authenticated;
drop policy if exists own_progress on public.police_progress;
create policy own_progress on public.police_progress for select to authenticated
  using ((select auth.uid()) = user_id);

-- Atomic compare-and-swap: an old device cannot silently replace newer data.
create or replace function public.save_police_progress(expected_revision bigint, new_payload jsonb)
returns bigint language plpgsql security definer set search_path = '' as $$
declare uid uuid := auth.uid(); current_revision bigint; next_revision bigint;
begin
  if uid is null then raise exception 'authentication required'; end if;
  if new_payload is null or new_payload->>'version' is distinct from '1'
     or jsonb_typeof(new_payload->'history') is distinct from 'array'
     or jsonb_typeof(new_payload->'attempts') is distinct from 'array'
     or octet_length(new_payload::text) > 2000000 then
    raise exception 'invalid progress';
  end if;
  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(uid::text, 0));
  select revision into current_revision from public.police_progress where user_id = uid;
  if coalesce(current_revision, 0) is distinct from expected_revision then
    raise exception 'PROGRESS_CONFLICT';
  end if;
  next_revision := coalesce(current_revision, 0) + 1;
  insert into public.police_progress(user_id, revision, payload)
    values(uid, next_revision, new_payload)
    on conflict (user_id) do update set revision = next_revision, payload = new_payload, updated_at = now();
  return next_revision;
end;
$$;
revoke all on function public.save_police_progress(bigint, jsonb) from public, anon;
grant execute on function public.save_police_progress(bigint, jsonb) to authenticated;
