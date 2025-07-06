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


    // --- Highlight Current Page in Nav ---
    const navLinks = document.querySelectorAll('.nav-links a');

    const highlightCurrentPage = () => {
        const currentPage = window.location.pathname.split('/').pop() || 'index.html';
        navLinks.forEach(link => {
            link.classList.remove('active');
            const linkPage = link.getAttribute('href');
            if (linkPage === currentPage) {
                link.classList.add('active');
            }
        });
    };

    highlightCurrentPage();

    // --- PDF Download ---
    const exportButton = document.getElementById('export-pdf');
    exportButton.addEventListener('click', () => {
        const lang = localStorage.getItem('language') || 'es';
        const pdfFile = lang === 'en' ? 'files/julio_madera_en.pdf' : 'files/julio_madera_es.pdf';
        window.open(pdfFile, '_blank');
    });

});