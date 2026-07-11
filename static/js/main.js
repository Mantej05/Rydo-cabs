// Nav toggle for mobile
document.getElementById('navToggle').addEventListener('click', function() {
  document.getElementById('navLinks').classList.toggle('open');
});

// Auto-dismiss messages
document.querySelectorAll('.msg').forEach(function(msg) {
  setTimeout(function() {
    msg.style.opacity = '0';
    msg.style.transition = 'opacity 0.5s';
    setTimeout(function() { msg.remove(); }, 500);
  }, 4000);
});
