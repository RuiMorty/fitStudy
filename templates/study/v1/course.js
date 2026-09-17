document.querySelectorAll('.flip').forEach((button) => {
  button.addEventListener('click', () => {
    const pressed = button.getAttribute('aria-pressed') !== 'true';
    button.setAttribute('aria-pressed', String(pressed));
    button.querySelector('.front').setAttribute('aria-hidden', String(pressed));
    button.querySelector('.back').setAttribute('aria-hidden', String(!pressed));
  });
});
document.querySelectorAll('.question').forEach((question) => {
  question.querySelector('.check').addEventListener('click', () => {
    const selected = [...question.querySelectorAll('input:checked')].map((input) => Number(input.value)).sort();
    const answer = question.querySelector('.answer');
    answer.hidden = false;
    if (!selected.length) { answer.textContent = '请先选择答案。'; delete question.dataset.result; return; }
    const correct = JSON.stringify(selected) === JSON.stringify(JSON.parse(question.dataset.answers).sort());
    question.dataset.result = correct ? 'correct' : 'wrong';
    answer.textContent = `${correct ? '回答正确。' : '再想一想。'}${question.dataset.explanation}`;
  });
});
const imageDialog = document.querySelector('dialog');
document.querySelectorAll('[data-zoom]').forEach((button) => {
  button.addEventListener('click', () => {
    const original = button.querySelector('img');
    const image = imageDialog.querySelector('img');
    image.src = original.src;
    image.alt = original.alt;
    imageDialog.showModal();
  });
});
imageDialog.querySelector('button').addEventListener('click', () => imageDialog.close());
imageDialog.addEventListener('click', (event) => {
  const rect = imageDialog.getBoundingClientRect();
  if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) imageDialog.close();
});
