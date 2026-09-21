// ===================================================
// TRƯỜNG THCS NGÔ VĂN SỞ - CLIENT INTERACTIONS SCRIPT
// ===================================================

document.addEventListener('DOMContentLoaded', function () {
  // 1. Live Vietnamese Clock
  const clockEl = document.getElementById('live-clock');
  if (clockEl) {
    function updateClock() {
      const days = ["Chủ nhật", "Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"];
      const now = new Date();
      const dayName = days[now.getDay()];
      const day = String(now.getDate()).padStart(2, '0');
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const year = now.getFullYear();
      const hours = String(now.getHours()).padStart(2, '0');
      const minutes = String(now.getMinutes()).padStart(2, '0');
      const seconds = String(now.getSeconds()).padStart(2, '0');

      clockEl.textContent = `${dayName}, ${day}/${month}/${year} ${hours}:${minutes}:${seconds}`;
    }
    updateClock();
    setInterval(updateClock, 1000);
  }

  // 2. Featured Article Slider
  const sliderItems = document.querySelectorAll('.slider-main-item');
  const navItems = document.querySelectorAll('.slider-nav-item');
  let currentSlide = 0;
  let slideInterval = null;

  function showSlide(index) {
    if (!sliderItems.length) return;
    sliderItems.forEach(item => item.classList.remove('active'));
    navItems.forEach(item => item.classList.remove('active'));

    currentSlide = (index + sliderItems.length) % sliderItems.length;
    sliderItems[currentSlide].classList.add('active');
    if (navItems[currentSlide]) {
      navItems[currentSlide].classList.add('active');
    }
  }

  if (sliderItems.length > 0) {
    navItems.forEach((item, idx) => {
      item.addEventListener('click', () => {
        showSlide(idx);
        resetInterval();
      });
      item.addEventListener('mouseenter', () => {
        showSlide(idx);
        clearInterval(slideInterval);
      });
      item.addEventListener('mouseleave', () => {
        startInterval();
      });
    });

    function startInterval() {
      slideInterval = setInterval(() => {
        showSlide(currentSlide + 1);
      }, 4500);
    }

    function resetInterval() {
      clearInterval(slideInterval);
      startInterval();
    }

    startInterval();
  }

  // 3. Back to Top Button
  const backToTopBtn = document.getElementById('backToTop');
  if (backToTopBtn) {
    window.addEventListener('scroll', function () {
      if (window.scrollY > 300) {
        backToTopBtn.classList.add('show');
      } else {
        backToTopBtn.classList.remove('show');
      }
    });

    backToTopBtn.addEventListener('click', function () {
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    });
  }

  // 4. Quick website selector redirect
  const websiteSelect = document.getElementById('quickWebsites');
  if (websiteSelect) {
    websiteSelect.addEventListener('change', function () {
      if (this.value) {
        window.open(this.value, '_blank');
      }
    });
  }
});
