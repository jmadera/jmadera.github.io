document.addEventListener('DOMContentLoaded', () => {

    // --- Language Switcher Spanish/English ---
    const langES = document.getElementById('lang-es');
    const langEN = document.getElementById('lang-en');
    const elementsES = document.querySelectorAll('.es');
    const elementsEN = document.querySelectorAll('.en');

    const setLanguage = (lang) => {
        if (lang === 'es') {
            elementsES.forEach(el => el.style.display = 'inline');
            elementsEN.forEach(el => el.style.display = 'none');
            langES.classList.add('active');
            langEN.classList.remove('active');
        } else {
            elementsES.forEach(el => el.style.display = 'none');
            elementsEN.forEach(el => el.style.display = 'inline');
            langEN.classList.add('active');
            langES.classList.remove('active');
        }
        localStorage.setItem('language', lang);
    };

    langES.addEventListener('click', () => setLanguage('es'));
    langEN.addEventListener('click', () => setLanguage('en'));

    // Load saved language or default to Spanish
    const savedLang = localStorage.getItem('language') || 'es';
    setLanguage(savedLang);


    // --- Active Nav Link on Scroll ---
    const sections = document.querySelectorAll('main section');
    const navLinks = document.querySelectorAll('.nav-links a');

    const activateNavLink = () => {
        let currentSectionId = '';
        const scrollPosition = window.scrollY;

        sections.forEach(section => {
            const sectionTop = section.offsetTop - 70; // Offset for fixed header
            if (scrollPosition >= sectionTop) {
                currentSectionId = section.getAttribute('id');
            }
        });
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${currentSectionId}`) {
                link.classList.add('active');
            }
        });
    };

    window.addEventListener('scroll', activateNavLink);
    activateNavLink(); // Set active link on page load

});