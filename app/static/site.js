document.addEventListener('DOMContentLoaded', () => {
  const menu = document.querySelector('[data-menu-toggle]');
  const sidebar = document.querySelector('.app-header');

  menu?.addEventListener('click', () => {
    const opened = sidebar.classList.toggle('open');
    menu.setAttribute('aria-expanded', String(opened));
  });

  document.addEventListener('click', (event) => {
    if (window.innerWidth <= 980 && sidebar?.classList.contains('open') &&
        !sidebar.contains(event.target) && !menu?.contains(event.target)) {
      sidebar.classList.remove('open');
      menu?.setAttribute('aria-expanded', 'false');
    }
  });

  document.querySelectorAll('.password-toggle').forEach((button) => {
    button.addEventListener('click', () => {
      const field = document.getElementById(button.dataset.target);
      const show = field.type === 'password';
      field.type = show ? 'text' : 'password';
      button.textContent = show ? 'Ocultar' : 'Mostrar';
      button.setAttribute('aria-label', show ? 'Ocultar senha' : 'Mostrar senha');
    });
  });

});
