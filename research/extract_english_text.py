import json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'tmp/english-ocr-text'

Q={
1:'A: 191 ______?\nB: I would like to report a robbery.',
2:"A: Excuse me, officer. I’ve lost my wallet. What should I do?\nB: ______, and then we can help you with the report.",
3:'A: Help! Someone just stole my phone!\nB: Which way did they go?\nA: ______',
4:'A: My dog was hit by a car this morning.\nB: Oh dear! ______',
5:'A: ______?\nB: No, I’ve only had some water and a soda tonight.\nA: I see, but I still need you to blow into this breathalyzer for a routine check.',
6:'A: Excuse me. ______\nB: Certainly.',
7:"A: ______?\nB: I'm sorry, I left it at home in my other jacket.\nA: In that case, I have to issue you a ticket for driving without a valid license.",
8:"A: ______?\nB: Oh, I’m sorry. My dog chewed it, but the information page is still readable.\nA: I'm afraid I cannot accept this. You need to contact your embassy for a new one.",
9:'A: What is the matter?\nB: ______\nA: What are your symptoms?\nB: I have a runny nose.',
10:'A: ______?\nB: About a year. I love it!\nA: Me too. It helps me relax to stay here.',
11:"A: ______?\nB: I have 500 dollars in cash and a credit card. Is that not enough?\nA: I'm sorry, but the regulation requires at least 20,000 baht in cash to enter.",
12:'A: Next, please.\nB: ______\nA: Single or return?',
13:"A: ______?\nB: I'm sorry, I didn't know the speed limit here was only 60 km/h.\nA: It’s clearly marked on the signs. May I see your license, please?",
14:'A: I have to appear in court next week.\nB: Why? Did you do something wrong?\nA: Of course not. ______',
15:'A: Good afternoon. Can I help you find anything?\nB: Yes, I’m looking for a gift for my daughter.\nA: ______\nB: She’s turning seven next week, and she loves drawing.',
16:'A: I forgot to pay the phone bill.\nB: ______\nA: Thanks. I really appreciate it.',
17:'A: Officer! There’s a car accident at the intersection! I think someone is hurt.\nB: ______\nA: Yes, please. A woman is bleeding from her head.',
18:"A: Next in line, please. What can I get for you?\nB: I'll have a large iced latte, please.\nA: ______\nB: For here, please. I have a bit of work to do.",
19:'A: I ran into John yesterday.\nB: ______\nA: Yes, he said he just moved back to town.',
20:"A: Guess what! I finally passed my driving test today!\nB: ______\nA: Thank you! I'm so relieved. Now I can finally drive to work.",
21:'A: While driving home last night, I was caught by a speed camera.\nB: Oh! ______?',
22:'A: Someone is helping the injured person over there. What does he do?\nB: ______. He happened to be passing by.',
23:"A: ______\nB: Hi, I'd like to book a table for four for this evening, please.\nA: ______\nB: Around 7:30 PM, if possible.",
24:'A: Please place your bags on the conveyor belt and remove your jacket.\nB: Sure. ______\nA: No, you can keep them on. Just make sure you have no liquids in your pockets.',
25:'A: This shirt looks great on you. Would you like to take it?\nB: It’s nice, but ______\nA: Of course. The fitting rooms are right over there.',
26:'My doctor advised me to get more exercise to improve my ______ health.',
27:'The police wear a uniform to be easily ______ in a crowd.',
28:'All passengers are required to ______ with the security regulations at the airport.',
29:"I'm allergic to pollen, so I have to take ______.",
30:'The witness provided a very ______ description of the suspect, which helped the police catch him quickly.',
31:'The police officer wrote down a detailed ______ of the crime scene.',
32:'A good police officer should be ______ and treat everyone with respect.',
33:'The manager needs to ______ the team on the upcoming project.',
34:'Your passport has ______, so you need to renew it before traveling abroad.',
35:'It is ______ to carry weapons or dangerous objects onto the airplane.',
36:'If you lose your passport, you should ______ it to the police immediately.',
37:'The police have the authority to ______ a vehicle suspected of carrying illegal goods.',
38:'Please ensure that all the information provided in this form is ______.',
39:'The immigration officer will ______ your passport to check for a valid visa.',
40:'Drivers must ______ the speed limit to ensure safety for everyone.',
41:'If a bag is left ______ at the airport, it will be removed by security.',
42:'The detective is looking for a ______ between the two crimes.',
43:'Police officers must maintain a high ______ of discipline.',
44:'An officer was praised for his ______ after returning a lost wallet full of money.',
45:'Parking is strictly ______ in front of the emergency entrance.',
46:'He got a ______ for speeding on the motorway.',
47:'Please renew your visa. It is no longer ______.',
48:'The department will ______ all applicants of the exam results via email next week.',
49:'Drivers who ______ the speed limit will be fined according to the law.',
50:'We appreciate your ______ in providing information regarding the case.',
51:'If you ______ your passport, you will have to contact the immigration office immediately.',
52:'The Japanese food at the new restaurant tasted really ______.',
53:'The new security system is ______ than the old one we used last year.',
54:'The man ______ car was stolen called the police. They still cannot find the location of his car.',
55:'The police officer saw the accident while he ______ his motorcycle to the station.',
56:'A suspicious package ______ by the guard near the entrance this morning.',
57:'If you had come to the police station, you ______ met instructor John.',
58:'The immigration office will be closed ______ public holidays.',
59:'The person ______ reported the crime preferred to remain anonymous.',
60:'______ the heavy rain, the police officers continued their search for the missing person.',
61:'The criminal ______ the building before the police arrived at the scene.',
62:'______ are always supporting me.',
63:"The suspect didn't admit to the crime, ______?",
64:'My cat is ______ than my dog.',
65:'Most of the information that ______ provided by the witness was found to be true.',
66:'My eyes are sore. I ______ for three hours. I should take a rest.',
67:'Please be patient. Your application ______ by the officer right now.',
68:'Ten kilometers ______ a long distance for the patrol officers to walk every day.',
69:'Never ______ such a complex cybercrime case before.',
70:'She advised me not ______ anything.',
71:'The suspect ran ______ the building and disappeared into the crowd.',
72:'It was raining, ______ we decided to stay home.',
73:'The chief of police insisted that every officer ______ the new safety regulations.',
74:'The witness was so scared that she could ______ speak to the police.',
75:'______ illegal drugs is a serious offense that can lead to life imprisonment.',
76:"Let’s discuss the evidence in the meeting room, ______?",
77:'You cough a lot. Quitting ______ will help you.',
78:'The investigator found ______ clues at the scene, making it difficult to solve the case.',
79:'The suspect eventually surrendered and turned ______ in to the authorities.',
80:"______ I had breakfast this morning, I'm still hungry and it's not even lunchtime.",
81:'What does this sign mean?',82:'What does this sign mean?',83:'What does this sign mean?',
84:'What does this sign mean?',85:'What does this sign mean?',
86:'Look at the town map and answer the question. From the ice cream shop, how can you go to the coffee shop?',
87:'Look at the town map and answer the question. Which sentence is correct?',
88:'Read the power-outage notice. What is the primary reason for the electricity interruption mentioned in the notice?',
96:'Read the weekend weather forecast. What is the weather like on Saturday morning?'
}

C={
4:['Everything must go!','You must be crazy!',"That’s a shame!",'I am not surprised!'],
5:['Are you feeling sick?','Have you been drinking any alcohol?','Did you see the car accident?','Is this your first time driving?'],
7:['Is this your car?','Did you forget something?','Where are you going in such a hurry?',"Do you have your driver's license with you?"],
8:['Why is your passport so dirty?','Did you bring your passport today?','May I ask why your passport is damaged?','Is this your real passport?'],
9:["I'm fine.","I don't feel well.",'I am very happy.','It is good.'],
10:['What brought you here today?','How long have you been coming here?','Have you read any good books lately?','Do you enjoy learning new things?'],
11:['How much money are you carrying with you?','Do you have any Thai Baht?',"Why don't you have more money?",'Can I see your credit card, please?'],
17:["That's too bad.",'Should I call an ambulance?','What is your phone number?',"Do you have a driver's license?"],
20:['Better luck next time.',"That's too bad.","Congratulations! I’m so happy for you.",'Why did you do that?'],
24:['Do I need to take off my shoes?','Is my bag too heavy?','Where is the waiting area?','Can I have some water?'],
34:['expanded','expired','expected','expressed'],35:['permitted','legal','prohibited','encouraged'],
36:['report','ignore','hide','forget'],37:['search','sell','paint','buy'],38:['fake','accurate','wrong','hidden'],
39:['ignore','examine','imagine','improve'],40:['break','change','ignore','observe'],42:['separation','connection','distance','difference'],
46:['fine','license','ticket','reward'],47:['beautiful','crowded','expensive','valid'],
51:['lose','lost','will lose','had lost'],52:['deliciously','delicioused','deliciousing','delicious'],
53:['as effective','effective','most effective','more effective'],54:['who','whom','which','whose'],
55:['riding','rides','was riding','has ridden'],56:['found','was found','has found','is finding'],
59:['whom','whose','who','which'],62:['I','He','They','Everyone'],63:["didn't he",'did he','was he','was be'],
65:['is','are','was','were'],67:['is reviewing','is being reviewed','reviewed','has reviewed'],68:['is','are','being','were'],
71:['out of','away of','off to','from out'],72:['so','or','but','and'],73:['follows','follow','followed','is following'],
74:['hardly','not hardly','hardly not','nearly'],75:['To smuggling','Smuggling','Smuggled','Smuggle'],
78:['a little','little','a few','few'],79:['him','himself','his','he'],
81:['Pedestrians must walk on the right side of the road.','Drivers should be careful because people may cross the street.','This area is only for people to exercise.','No entry for people on foot.'],
82:['You must not turn left.','You must not change lanes or overtake other vehicles.','Drivers can speed up in this area.','One-way traffic only.'],
83:['You can drive over 120 km/h.','You can drive faster than 120 km/h.',"You can’t drive faster than 120 km/h.","You can’t drive slower than 120 km/h."],
84:['You can enter and fix things here.','This place is not open because it is being repaired.','This shop is closed forever.','You should be quiet in this area.'],
85:['Maximum speed limit is 50 km/h.','You must drive at a speed of at least 50 km/h.','There are 50 parking spaces ahead.','The distance to the next city is 50 km.'],
86:["Go straight on Peanut Road. It’s on your right opposite the lake.","Go straight on Peanut Road and turn left on Lucky Road. It’s on your left next to the theater.","Turn left onto Pumpkin Road and turn right onto Cherry Road. It’s on your left next to the gym.","Turn left onto Pumpkin Road. It’s on your right opposite the hospital."],
88:['To fix a broken power pole after an accident.','To install new equipment for system reliability.','To encourage residents to save energy.','To move cables underground during the night.'],
90:['They use weapons to threaten victims.','They work alone to avoid being caught.','They try to distract people before stealing.','They follow victims to their homes.'],
94:['It helps police find new witnesses.','It can solve crimes that have been unsolved for a long time.','It prevents crimes from happening.','It makes the investigation process faster than before.'],
95:['To describe the different types of street food available in Thailand.','To explain how to cook Thai food.','To compare Thai street food to other types of cuisine.','To encourage people to try street food in Thailand.'],
96:['Hot and humid.','Rainy and windy.','Cold with some fog.','Cloudy with no sun.'],
99:['It stops working completely to save energy.','It clears out toxins and organizes memories.','It dreams about future events to prevent stress.','It monitors the surroundings for danger.'],
100:['He was seriously injured and required surgery.','He was the one who failed the sobriety test.','He was entering the intersection legally.','He fled the scene before the police arrived.']
}

P={
88:'NOTICE OF POWER OUTAGE\nThe Metropolitan Electricity Authority (MEA) will temporarily interrupt electricity supply on Sunday, March 22, 2026, from 8:00 AM to 4:00 PM. This outage is necessary for the installation of new high-voltage cables and maintenance of the power distribution system to ensure long-term reliability.\nAffected areas: Sukhumvit Soi 21 to Soi 23; Asoke Montri Road (northbound side only).\nResidents and businesses in these areas are advised to unplug sensitive electronic devices to prevent damage from power surges when electricity is restored.',
96:'WEEKEND WEATHER\nThe Meteorological Department has released the forecast for the upcoming weekend. A high-pressure system from the north is moving across the region, resulting in a significant drop in temperature.\nSaturday: Most areas will experience chilly weather in the early morning with some light fog. However, the skies will be clear and sunny during the afternoon. The maximum temperature will be around 25°C.\nSunday: The weather will become more unpredictable. There is a 60% chance of isolated thunderstorms and heavy rain in the evening. Residents are advised to carry an umbrella and drive with caution due to slippery roads. Small boats should remain ashore as strong winds are expected in coastal areas.'
}

PROMPTS={
89:'What happened to Mr. Robert Smith at the railway station?',
90:'According to the notice, what is a technique used by thieves?',
91:'What do the scammers claim when they contact the victims?',
92:'What was the main objective of the “Safe Streets” operation?',
93:'What will happen to cars that break the new rules?',
94:'Why is DNA profiling useful for “cold cases”?',
95:'What is the main point of the passage?',
97:'What is the main cause of the flood watch?',
98:'What should an interested person do to apply for this job?',
99:'According to the text, what does the brain do during sleep?',
100:'Which of the following is TRUE about the truck driver?'
}

PASSAGE_START={89:'incident Report Date:',90:'IMPORTANT PUBLIC NOTICE',91:'Police Warn Public',92:'Police Seize Illegal Weapons',93:'OFFICE OF THE DISTRICT POLICE',94:'The Power of DNA Profiling',95:"Thailand's vibrant streets",97:'EMERGENCY BULLETIN',98:'JOB VACANCY',99:'why Sleep Matters',100:'INCIDENT REPORT: VEHICLE COLLISION'}

def clean(s):
    s=s.replace('\r','').replace('|','I')
    s=re.sub(r'\s+',' ',s).strip(' -_/')
    return s

def parse(n):
    lines=[clean(x) for x in (RAW/f'q{n:03}.txt').read_text(encoding='utf-8',errors='ignore').splitlines()]
    lines=[x for x in lines if x]
    start=next((i for i,x in enumerate(lines) if re.match(rf'^{n}[.,]?\s+',x)),None)
    if start is not None:
        lines=lines[start:]
        lines[0]=re.sub(rf'^{n}[.,]?\s*','',lines[0])
    hits=[]
    for i,x in enumerate(lines):
        m=re.match(r'^([1-4])[.,;)]\s*(.*)',x)
        if m: hits.append((i,int(m.group(1)),m.group(2)))
    # Find the last complete ordered 1-4 sequence. This avoids header/page-number noise.
    chosen=None
    for a in range(len(hits)):
        seq=[];expect=1
        for hit in hits[a:]:
            if hit[1]==expect:
                seq.append(hit);expect+=1
                if expect==5: chosen=seq
            elif hit[1]==1:
                seq=[hit];expect=2
    if not chosen:
        result={'question':' '.join(lines),'choices':{},'parsed':False,'reading_passage':P.get(n)}
        if n in Q and n in C: result={'question':Q[n],'choices':dict(zip('ABCD',C[n])),'parsed':True}
        return result
    qend=chosen[0][0]
    question=clean(' '.join(lines[:qend]))
    choices={}
    for j,(idx,num,first) in enumerate(chosen):
        end=chosen[j+1][0] if j<3 else len(lines)
        choices['ABCD'[num-1]]=clean(' '.join([first]+lines[idx+1:end]))
    if n in Q: question=Q[n]
    if n in C: choices=dict(zip('ABCD',C[n]))
    fixes={'vehictes':'vehicles','Maxirnum':'Maximum','km/N':'km/h','eqlain':'explain','avs':'arrived','Set. Anan':'Sgt. Anan','arrivat':'arrival','tegatly':'legally'}
    for a,b in fixes.items():
        question=question.replace(a,b)
        choices={k:v.replace(a,b) for k,v in choices.items()}
    passage=P.get(n)
    if n in PROMPTS:
        lead=' '.join(PROMPTS[n].split()[:5])
        marker=next((m for m in [PROMPTS[n],PROMPTS[n].replace('“','"').replace('”','"'),lead] if m in question),None)
        if marker:
            passage=question[:question.index(marker)].strip()
        start=PASSAGE_START[n]
        at=passage.lower().find(start.lower()) if passage else -1
        if at>=0: passage=passage[at:]
        question=PROMPTS[n]
    if passage:
        passage_fixes={'incident Report':'Incident Report','if you':'If you','in a large scale':'In a large-scale','month-tong':'month-long','including legal possession':'including illegal possession','subject:':'Subject:','wilt implement':'will implement','bite: szed':'bite-sized','fiends':'friends','creates 4 unique':'creates a unique','and sia ona':'and set off on a','giverside Basin':'Riverside Basin','please move':'Please move','issued by:':'Issued by:','status:':'Status:','Atleast':'At least','Global protection':'Global Protection','why Sleep Matters':'Why Sleep Matters','Mong peonie See':'Many people see','it is 3 fundamental':'it is a fundamental','far en inactive':'far from inactive','poo! concentration':'poor concentration','stower reaction':'slower reaction','help the body sala melatonin, i aii responsible for sleep':'help the body produce melatonin, a hormone responsible for sleep','arrival ival.':'arrival,','damage According':'damage. According'}
        for a,b in passage_fixes.items(): passage=passage.replace(a,b)
    return {'question':question,'choices':choices,'parsed':True,'reading_passage':passage}

if __name__=='__main__':
    data={str(n):parse(n) for n in range(1,101)}
    (ROOT/'tmp/english-parsed.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    for n,x in data.items():
        print(n, x['parsed'], x['question'][:110], list(x['choices'].values()))
