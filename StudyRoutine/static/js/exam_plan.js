(function () {
  const panel = document.getElementById('plan-panel');
  const toggleBtn = document.getElementById('toggle-plan-panel');
  const closeBtn = document.getElementById('close-plan-panel');
  const buildBtn = document.getElementById('build-plan-btn');
  const buildForm = document.getElementById('build-plan-form');
  const rebuildModal = document.getElementById('rebuild-modal');
  const rebuildCancel = document.getElementById('rebuild-cancel');

  function openPanel() {
    if (!panel) return;
    panel.classList.add('is-open');
    panel.setAttribute('aria-hidden', 'false');
  }

  function closePanel() {
    if (!panel) return;
    panel.classList.remove('is-open');
    panel.setAttribute('aria-hidden', 'true');
  }

  if (toggleBtn) {
    toggleBtn.addEventListener('click', function () {
      if (panel.classList.contains('is-open')) {
        closePanel();
      } else {
        openPanel();
      }
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener('click', closePanel);
  }

  if (buildBtn && buildForm) {
    buildBtn.addEventListener('click', function () {
      const hasPlan = buildBtn.getAttribute('data-has-plan') === '1';
      if (hasPlan && rebuildModal) {
        rebuildModal.removeAttribute('hidden');
        return;
      }
      buildForm.submit();
    });
  }

  if (rebuildCancel && rebuildModal) {
    rebuildCancel.addEventListener('click', function () {
      rebuildModal.setAttribute('hidden', '');
    });
  }

  if (rebuildModal) {
    rebuildModal.addEventListener('click', function (event) {
      if (event.target === rebuildModal) {
        rebuildModal.setAttribute('hidden', '');
      }
    });
  }
})();
