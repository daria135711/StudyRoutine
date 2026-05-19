/**
 * Pomodoro timer: 25 min focus / 5 min break.
 * Init on any element with [data-pomodoro].
 */
(function () {
    'use strict';

    const WORK_SEC = 25 * 60;
    const BREAK_SEC = 5 * 60;

    function formatTime(seconds) {
        const m = Math.floor(seconds / 60);
        const s = seconds % 60;
        return String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
    }

    function initPomodoro(root) {
        const display = root.querySelector('[data-pomo-time]');
        const label = root.querySelector('[data-pomo-label]');
        const ring = root.querySelector('[data-pomo-ring]');
        const btnStart = root.querySelector('[data-pomo-start]');
        const btnPause = root.querySelector('[data-pomo-pause]');
        const btnReset = root.querySelector('[data-pomo-reset]');
        const minutesInput = document.getElementById('session-minutes');
        const topicSelect = root.querySelector('[data-pomo-topic]');

        if (!display || !btnStart || !btnPause || !btnReset) {
            return;
        }

        let mode = 'work';
        let remaining = WORK_SEC;
        let segmentTotal = WORK_SEC;
        let timerId = null;
        let workMinutesDone = 0;

        function updateRing() {
            if (!ring) return;
            const ratio = segmentTotal > 0 ? remaining / segmentTotal : 0;
            const deg = Math.max(0, Math.min(360, Math.round(ratio * 360)));
            ring.style.setProperty('--pomo-deg', deg + 'deg');
        }

        function setActiveButton(activeBtn) {
            [btnStart, btnPause, btnReset].forEach(function (btn) {
                btn.classList.remove('active');
            });
            if (activeBtn) activeBtn.classList.add('active');
        }

        function render() {
            display.textContent = formatTime(remaining);
            if (label) {
                label.textContent = mode === 'work' ? 'фокус' : 'перерыв';
            }
            updateRing();
        }

        function switchMode() {
            if (mode === 'work') {
                workMinutesDone += 25;
                if (minutesInput) {
                    minutesInput.value = String(workMinutesDone || 25);
                }
            }
            mode = mode === 'work' ? 'break' : 'work';
            segmentTotal = mode === 'work' ? WORK_SEC : BREAK_SEC;
            remaining = segmentTotal;
            render();
        }

        function tick() {
            if (remaining <= 0) {
                clearInterval(timerId);
                timerId = null;
                switchMode();
                setActiveButton(null);
                if (typeof window !== 'undefined' && window.Notification && Notification.permission === 'granted') {
                    new Notification('StudyRoutine', {
                        body: mode === 'work' ? 'Время перерыва!' : 'Время сфокусироваться!',
                    });
                }
                return;
            }
            remaining -= 1;
            render();
        }

        btnStart.addEventListener('click', function () {
            if (timerId) return;
            if (topicSelect && !topicSelect.value) {
                topicSelect.focus();
                return;
            }
            timerId = setInterval(tick, 1000);
            setActiveButton(btnStart);
        });

        btnPause.addEventListener('click', function () {
            if (timerId) {
                clearInterval(timerId);
                timerId = null;
            }
            setActiveButton(btnPause);
        });

        btnReset.addEventListener('click', function () {
            if (timerId) {
                clearInterval(timerId);
                timerId = null;
            }
            mode = 'work';
            segmentTotal = WORK_SEC;
            remaining = WORK_SEC;
            workMinutesDone = 0;
            if (minutesInput) minutesInput.value = '25';
            render();
            setActiveButton(null);
        });

        if (topicSelect && minutesInput) {
            topicSelect.addEventListener('change', function () {
                minutesInput.value = String(workMinutesDone || 25);
            });
        }

        render();
        setActiveButton(null);
    }

    function boot() {
        document.querySelectorAll('[data-pomodoro]').forEach(initPomodoro);
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})();
