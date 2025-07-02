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

    // --- PDF Export --- 
    const exportButton = document.getElementById('export-pdf');
    exportButton.addEventListener('click', () => {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF('p', 'pt', 'a4');
        const mainContent = document.querySelector('.main-content');

        html2canvas(mainContent, {
            useCORS: true,
            scale: 2, // Aumenta la resolución de la imagen
        }).then(canvas => {
            const imgData = canvas.toDataURL('image/png');
            const imgProps = doc.getImageProperties(imgData);
            const pdfWidth = doc.internal.pageSize.getWidth();
            const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;
            let heightLeft = pdfHeight;
            let position = 0;

            doc.addImage(imgData, 'PNG', 0, position, pdfWidth, pdfHeight);
            heightLeft -= doc.internal.pageSize.getHeight();

            while (heightLeft >= 0) {
                position = heightLeft - pdfHeight;
                doc.addPage();
                doc.addImage(imgData, 'PNG', 0, position, pdfWidth, pdfHeight);
                heightLeft -= doc.internal.pageSize.getHeight();
            }

            doc.save('juliocesar_madera_quintana.pdf');
        });
    });

});