(function () {
  const data = window.POLICE_DATA;
  if (!data) return;

  const folders = {
    it: 'assets/real-computer-explanations',
    law: 'assets/real-law-explanations',
    social: 'assets/real-social-explanations',
    thai: 'assets/real-thai-explanations'
  };

  for (const question of data.questions) {
    if (question.representation !== 'actual' || !folders[question.subject]) continue;
    const number = String(question.question_number).padStart(3, '0');
    question.explanation_image = `${folders[question.subject]}/q${number}.jpg`;
    question.explanation_author = 'source';
    if (question.subject !== 'it' && question.subject !== 'thai') {
      question.explanation_th = ['ดูเหตุผลของแต่ละตัวเลือกและคำอธิบายละเอียดจากเอกสารเฉลยด้านล่าง'];
    }
  }
})();
