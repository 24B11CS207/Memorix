// DQMS shared JS

document.addEventListener('DOMContentLoaded', () => {
  // Auto-dismiss flash messages after 5s
  document.querySelectorAll('.alert.alert-dismissible').forEach(a => {
    setTimeout(() => {
      try { bootstrap.Alert.getOrCreateInstance(a).close(); } catch (e) {}
    }, 5000);
  });

  // Highlight selected quiz option
  document.querySelectorAll('.option-row input[type=radio]').forEach(input => {
    input.addEventListener('change', () => {
      const name = input.name;
      document.querySelectorAll(`.option-row input[name=${name}]`).forEach(i => {
        i.closest('.option-row').classList.remove('border-info');
      });
      input.closest('.option-row').classList.add('border-info');
    });
  });

  // Confirm before submitting if there are unanswered questions
  const quizForm = document.getElementById('quizForm');
  if (quizForm) {
    quizForm.addEventListener('submit', (e) => {
      const groups = new Set();
      quizForm.querySelectorAll('input[type=radio]').forEach(r => groups.add(r.name));
      let unanswered = 0;
      groups.forEach(g => {
        if (!quizForm.querySelector(`input[name="${g}"]:checked`)) unanswered++;
      });
      if (unanswered > 0) {
        if (!confirm(`You have ${unanswered} unanswered question(s). Submit anyway?`)) {
          e.preventDefault();
        }
      }
    });
  }
});
