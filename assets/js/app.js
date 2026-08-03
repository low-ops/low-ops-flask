const PeopleApp = (() => {
  const API = '/api/users/';

  function escapeHtml(value = '') {
    return String(value)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#39;');
  }

  function initials(name = '') {
    return name
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase() || '')
      .join('') || '?';
  }

  function showToast(message) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(showToast._timer);
    showToast._timer = setTimeout(() => toast.classList.remove('show'), 2400);
  }

  async function request(url, options = {}) {
    const response = await fetch(url, options);
    if (response.status === 204) return null;
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const message =
        data.detail ||
        Object.values(data).flat?.().join(' ') ||
        'Something went wrong';
      throw new Error(typeof message === 'string' ? message : 'Something went wrong');
    }
    return data;
  }

  function avatarMarkup(user, className = 'avatar') {
    if (user.avatar) {
      return `<img class="${className}" src="${user.avatar}" alt="">`;
    }
    return `<span class="avatar-fallback ${className}">${initials(user.name)}</span>`;
  }

  function setButtonBusy(button, busy, label) {
    if (!button) return;
    if (busy) {
      button.dataset.label = button.textContent;
      button.textContent = label;
      button.disabled = true;
    } else {
      button.textContent = button.dataset.label || button.textContent;
      button.disabled = false;
    }
  }

  async function initHome() {
    const listEl = document.getElementById('people-list');
    const emptyEl = document.getElementById('empty-state');
    const loadingEl = document.getElementById('loading-state');
    const countEl = document.getElementById('count');
    const searchEl = document.getElementById('search');
    const sheet = document.getElementById('create-sheet');
    const form = document.getElementById('create-form');
    const openBtn = document.getElementById('open-create');
    const createBtn = document.getElementById('create-submit');

    let people = [];

    function render() {
      const query = (searchEl.value || '').trim().toLowerCase();
      const filtered = people.filter((person) => {
        const haystack = `${person.name} ${person.email}`.toLowerCase();
        return haystack.includes(query);
      });

      countEl.textContent = filtered.length === 1
        ? '1 person'
        : `${filtered.length} people`;

      listEl.innerHTML = filtered
        .map(
          (person, index) => `
            <a class="person-row" role="listitem" href="/users/${person.id}/" style="animation-delay: ${Math.min(index, 8) * 45}ms">
              ${avatarMarkup(person)}
              <div class="person-meta">
                <p class="person-name">${escapeHtml(person.name)}</p>
                <p class="person-email">${escapeHtml(person.email)}</p>
              </div>
              <span class="person-chevron" aria-hidden="true">→</span>
            </a>
          `
        )
        .join('');

      if (filtered.length > 0) {
        emptyEl.classList.add('hidden');
      } else {
        emptyEl.classList.remove('hidden');
        if (people.length === 0) {
          emptyEl.querySelector('h3').textContent = 'No people yet';
          emptyEl.querySelector('p').textContent = 'Add the first person to get started.';
        } else {
          emptyEl.querySelector('h3').textContent = 'No one matches';
          emptyEl.querySelector('p').textContent = 'Try another search, or add someone new.';
        }
      }
    }

    async function load() {
      try {
        people = await request(API);
        loadingEl.classList.add('hidden');
        render();
      } catch (error) {
        loadingEl.textContent = error.message;
      }
    }

    openBtn.addEventListener('click', () => sheet.showModal());
    searchEl.addEventListener('input', render);

    createBtn.addEventListener('click', async () => {
      const data = new FormData(form);
      if (!data.get('name') || !data.get('email')) {
        form.reportValidity();
        return;
      }
      if (!data.get('avatar_file')?.name) {
        data.delete('avatar_file');
      }

      setButtonBusy(createBtn, true, 'Creating…');
      try {
        await request(API, { method: 'POST', body: data });
        form.reset();
        sheet.close();
        showToast('Person added');
        await load();
      } catch (error) {
        showToast(error.message);
      } finally {
        setButtonBusy(createBtn, false);
      }
    });

    load();
  }

  async function initDetail() {
    const root = document.getElementById('detail');
    const userId = root.dataset.userId;
    const loadingEl = document.getElementById('detail-loading');
    const contentEl = document.getElementById('detail-content');
    const errorEl = document.getElementById('detail-error');
    const form = document.getElementById('detail-form');
    const saveBtn = document.getElementById('save-btn');
    const deleteBtn = document.getElementById('delete-btn');
    const confirmDeleteBtn = document.getElementById('confirm-delete');
    const deleteSheet = document.getElementById('delete-sheet');
    const avatarButton = document.getElementById('avatar-button');
    const avatarInput = document.getElementById('avatar-input');
    const avatarImage = document.getElementById('avatar-image');
    const avatarFallback = document.getElementById('avatar-fallback');
    const avatarHint = document.getElementById('avatar-hint');
    const nameEl = document.getElementById('detail-name');
    const emailEl = document.getElementById('detail-email');
    const nameInput = document.getElementById('input-name');
    const emailInput = document.getElementById('input-email');

    function paint(user) {
      nameEl.textContent = user.name;
      emailEl.textContent = user.email;
      nameInput.value = user.name;
      emailInput.value = user.email;
      avatarFallback.textContent = initials(user.name);
      document.title = `${user.name} · Low-Ops`;

      if (user.avatar) {
        avatarImage.src = user.avatar;
        avatarImage.alt = `${user.name} photo`;
        avatarImage.classList.remove('hidden');
        avatarFallback.classList.add('hidden');
      } else {
        avatarImage.classList.add('hidden');
        avatarFallback.classList.remove('hidden');
      }
    }

    async function load() {
      try {
        const user = await request(`${API}${userId}/`);
        paint(user);
        loadingEl.classList.add('hidden');
        contentEl.classList.remove('hidden');
      } catch (error) {
        loadingEl.classList.add('hidden');
        errorEl.classList.remove('hidden');
      }
    }

    avatarButton.addEventListener('click', () => avatarInput.click());

    avatarInput.addEventListener('change', async () => {
      const file = avatarInput.files?.[0];
      if (!file) return;

      const data = new FormData();
      data.append('avatar_file', file);
      avatarHint.textContent = 'Uploading photo…';

      try {
        const user = await request(`${API}${userId}/`, { method: 'PATCH', body: data });
        paint(user);
        showToast('Photo updated');
        avatarHint.textContent = 'JPG, PNG, or WebP';
      } catch (error) {
        showToast(error.message);
        avatarHint.textContent = 'Could not update photo';
      } finally {
        avatarInput.value = '';
      }
    });

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      setButtonBusy(saveBtn, true, 'Saving…');
      try {
        const user = await request(`${API}${userId}/`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: nameInput.value.trim(),
            email: emailInput.value.trim(),
          }),
        });
        paint(user);
        showToast('Changes saved');
      } catch (error) {
        showToast(error.message);
      } finally {
        setButtonBusy(saveBtn, false);
      }
    });

    deleteBtn.addEventListener('click', () => deleteSheet.showModal());

    confirmDeleteBtn.addEventListener('click', async () => {
      setButtonBusy(confirmDeleteBtn, true, 'Deleting…');
      try {
        await request(`${API}${userId}/`, { method: 'DELETE' });
        showToast('Person deleted');
        window.location.href = '/';
      } catch (error) {
        showToast(error.message);
        setButtonBusy(confirmDeleteBtn, false);
      }
    });

    load();
  }

  return { initHome, initDetail };
})();
