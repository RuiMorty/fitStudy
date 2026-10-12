// Keep the native selects as the application's data interface.
for (const select of document.querySelectorAll('.structure-panel select, .detail select')) {
  const label = document.querySelector(`label[for="${select.id}"]`);
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'select-trigger';
  button.id = `${select.id}-trigger`;
  button.setAttribute('aria-haspopup', 'listbox');
  button.setAttribute('aria-expanded', 'false');
  const menu = document.createElement('div');
  menu.className = 'select-menu';
  menu.id = `${select.id}-menu`;
  menu.setAttribute('role', 'listbox');
  menu.setAttribute('aria-label', label?.textContent || '选择');
  menu.hidden = true;
  button.setAttribute('aria-controls', menu.id);
  select.after(button);
  document.body.append(menu);
  select.hidden = true;
  if (label) label.htmlFor = button.id;
  let active = 0;
  const sync = () => {
    button.textContent = select.selectedOptions[0]?.textContent || '请选择';
    button.setAttribute('aria-label', `${label?.textContent || '选择'}：${button.textContent}`);
  };
  const close = () => { menu.hidden = true; button.setAttribute('aria-expanded', 'false'); button.removeAttribute('aria-activedescendant'); };
  const highlight = () => {
    [...menu.children].forEach((item, i) => item.classList.toggle('active', i === active));
    const item = menu.children[active];
    if (item) { button.setAttribute('aria-activedescendant', item.id); item.scrollIntoView({block:'nearest'}); }
  };
  const choose = i => {
    select.selectedIndex = i;
    select.dispatchEvent(new Event('change', {bubbles:true}));
    sync(); close(); button.focus();
  };
  const open = () => {
    document.dispatchEvent(new CustomEvent('select-opening'));
    menu.replaceChildren();
    [...select.options].forEach((option, i) => {
      const item = document.createElement('div');
      item.id = `${menu.id}-${i}`;
      item.setAttribute('role', 'option');
      item.setAttribute('aria-selected', String(option.selected));
      item.textContent = option.textContent;
      item.addEventListener('click', () => choose(i));
      menu.append(item);
    });
    const rect = button.getBoundingClientRect();
    menu.style.left = `${rect.left}px`;
    menu.style.width = `${rect.width}px`;
    const below = innerHeight - rect.bottom - 16;
    const above = rect.top - 16;
    const upward = below < Math.min(300, select.options.length * 44 + 12) && above > below;
    menu.style.top = upward ? 'auto' : `${rect.bottom + 8}px`;
    menu.style.bottom = upward ? `${innerHeight - rect.top + 8}px` : 'auto';
    menu.style.maxHeight = `${Math.min(360, upward ? above : below)}px`;
    menu.hidden = false;
    button.setAttribute('aria-expanded', 'true');
    active = select.selectedIndex;
    highlight();
  };
  button.addEventListener('click', () => menu.hidden ? open() : close());
  button.addEventListener('keydown', e => {
    if (['ArrowDown','ArrowUp','Home','End'].includes(e.key)) {
      e.preventDefault();
      if (menu.hidden) open();
      else { active = e.key === 'Home' ? 0 : e.key === 'End' ? select.options.length - 1 : Math.max(0, Math.min(select.options.length-1, active + (e.key === 'ArrowDown' ? 1 : -1))); highlight(); }
    } else if ((e.key === 'Enter' || e.key === ' ') && !menu.hidden) { e.preventDefault(); choose(active); }
    else if (e.key === 'Escape') { e.preventDefault(); close(); }
    else if (e.key === 'Tab') close();
  });
  document.addEventListener('pointerdown', e => { if (!menu.contains(e.target) && !button.contains(e.target)) close(); });
  document.addEventListener('focusin', e => { if (e.target !== button && !menu.contains(e.target)) close(); });
  document.addEventListener('select-opening', close);
  window.addEventListener('resize', close);
  document.addEventListener('scroll', e => { if (e.target !== menu) close(); }, true);
  select.addEventListener('change', sync);
  new MutationObserver(sync).observe(select, {childList:true, subtree:true, characterData:true});
  sync();
}
