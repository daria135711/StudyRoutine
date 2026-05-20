(function () {
  const board = document.getElementById('kanban-board');
  if (!board) return;

  const updateUrl = board.dataset.updateUrl;
  const csrfToken = board.dataset.csrf;

  function getColumnStatus(column) {
    return column.dataset.status;
  }

  function updateEmptyStates() {
    board.querySelectorAll('.kanban-column-body').forEach(function (body) {
      const hasCards = body.querySelector('.kanban-card');
      const empty = body.querySelector('.kanban-empty');
      if (empty) {
        empty.hidden = !!hasCards;
      }
    });
  }

  function postStatus(taskId, taskType, status) {
    const body = new FormData();
    body.append('task_id', taskId);
    body.append('task_type', taskType);
    body.append('status', status);
    return fetch(updateUrl, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken },
      body: body,
    }).then(function (r) {
      return r.json();
    });
  }

  board.querySelectorAll('.kanban-card').forEach(function (card) {
    card.addEventListener('dragstart', function (e) {
      card.classList.add('dragging');
      e.dataTransfer.setData(
        'text/plain',
        JSON.stringify({
          id: card.dataset.id,
          type: card.dataset.type,
        }),
      );
      e.dataTransfer.effectAllowed = 'move';
    });

    card.addEventListener('dragend', function () {
      card.classList.remove('dragging');
      board.querySelectorAll('.kanban-column-body').forEach(function (col) {
        col.classList.remove('drag-over');
      });
    });
  });

  board.querySelectorAll('.kanban-column-body').forEach(function (column) {
    column.addEventListener('dragover', function (e) {
      e.preventDefault();
      column.classList.add('drag-over');
    });

    column.addEventListener('dragleave', function () {
      column.classList.remove('drag-over');
    });

    column.addEventListener('drop', function (e) {
      e.preventDefault();
      column.classList.remove('drag-over');
      let payload;
      try {
        payload = JSON.parse(e.dataTransfer.getData('text/plain'));
      } catch (err) {
        return;
      }
      const card = board.querySelector(
        '.kanban-card[data-id="' + payload.id + '"][data-type="' + payload.type + '"]',
      );
      if (!card) return;

      const newStatus = getColumnStatus(column.closest('.kanban-column'));
      const oldColumn = card.closest('.kanban-column-body');

      column.appendChild(card);
      updateEmptyStates();

      postStatus(payload.id, payload.type, newStatus).then(function (data) {
        if (!data.ok) {
          oldColumn.appendChild(card);
          updateEmptyStates();
          alert(data.error || 'Не удалось обновить статус');
        } else {
          window.dispatchEvent(new CustomEvent('studyroutine:stats-changed'));
        }
      }).catch(function () {
        oldColumn.appendChild(card);
        updateEmptyStates();
        alert('Ошибка сети');
      });
    });
  });

  updateEmptyStates();
})();
