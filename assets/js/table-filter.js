// Table filtering and sorting functionality
document.addEventListener('DOMContentLoaded', function() {
    const table = document.getElementById('publications-table');
    const yearFilter = document.getElementById('year-filter');
    const typeFilter = document.getElementById('type-filter');
    const searchInput = document.getElementById('search-input');
    const exportBtn = document.getElementById('export-bibtex');
    const toggleDoiBtn = document.getElementById('toggle-doi');

    if (table) {
        // Populate year filter
        const years = new Set();
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const year = row.getAttribute('data-year');
            if (year) years.add(year);
        });

        if (yearFilter) {
            Array.from(years).sort().reverse().forEach(year => {
                const option = document.createElement('option');
                option.value = year;
                option.textContent = year;
                yearFilter.appendChild(option);
            });

            // Filter functionality
            yearFilter.addEventListener('change', filterTable);
        }

        if (typeFilter) {
            typeFilter.addEventListener('change', filterTable);
        }

        if (searchInput) {
            searchInput.addEventListener('input', filterTable);
        }

        // DOI toggle functionality
        if (toggleDoiBtn) {
            let doiVisible = false;
            toggleDoiBtn.addEventListener('click', function() {
                doiVisible = !doiVisible;
                const doiLinks = document.querySelectorAll('.doi-link');
                doiLinks.forEach(link => {
                    link.style.display = doiVisible ? 'inline' : 'none';
                });
                toggleDoiBtn.textContent = doiVisible ? 'Hide DOI' : 'Show DOI';
            });
        }

        // Sorting functionality
        const headers = table.querySelectorAll('th[data-sort]');
        headers.forEach(header => {
            header.addEventListener('click', function() {
                const sortKey = this.getAttribute('data-sort');
                sortTable(sortKey);
            });
        });

        // Export BibTeX
        if (exportBtn) {
            exportBtn.addEventListener('click', exportBibTeX);
        }
    }

    // Talks filtering
    const talksYearFilter = document.querySelector('.talks-controls #year-filter');
    const talksSearchInput = document.querySelector('.talks-controls #search-input');

    if (talksYearFilter || talksSearchInput) {
        const talkItems = document.querySelectorAll('.talk-item');

        // Populate year filter for talks
        if (talksYearFilter) {
            const years = new Set();
            talkItems.forEach(item => {
                const year = item.getAttribute('data-year');
                if (year) years.add(year);
            });

            Array.from(years).sort().reverse().forEach(year => {
                const option = document.createElement('option');
                option.value = year;
                option.textContent = year;
                talksYearFilter.appendChild(option);
            });

            talksYearFilter.addEventListener('change', filterTalks);
        }

        if (talksSearchInput) {
            talksSearchInput.addEventListener('input', filterTalks);
        }
    }

    function filterTable() {
        const yearValue = yearFilter ? yearFilter.value : '';
        const typeValue = typeFilter ? typeFilter.value : '';
        const searchValue = searchInput ? searchInput.value.toLowerCase() : '';

        rows.forEach(row => {
            const year = row.getAttribute('data-year');
            const type = row.getAttribute('data-type');
            const text = row.textContent.toLowerCase();

            const yearMatch = !yearValue || year === yearValue;
            const typeMatch = !typeValue || type === typeValue;
            const searchMatch = !searchValue || text.includes(searchValue);

            if (yearMatch && typeMatch && searchMatch) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    function sortTable(sortKey) {
        const tbody = table.querySelector('tbody');
        const rowsArray = Array.from(rows);

        rowsArray.sort((a, b) => {
            let aValue, bValue;

            if (sortKey === 'date') {
                aValue = a.querySelector('td[data-sort-value]').getAttribute('data-sort-value');
                bValue = b.querySelector('td[data-sort-value]').getAttribute('data-sort-value');
            } else {
                const aIndex = sortKey === 'title' ? 1 : 2;
                aValue = a.querySelectorAll('td')[aIndex].textContent.toLowerCase();
                bValue = b.querySelectorAll('td')[aIndex].textContent.toLowerCase();
            }

            return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
        });

        rowsArray.forEach(row => tbody.appendChild(row));
    }

    function filterTalks() {
        const yearValue = talksYearFilter ? talksYearFilter.value : '';
        const searchValue = talksSearchInput ? talksSearchInput.value.toLowerCase() : '';
        const talkItems = document.querySelectorAll('.talk-item');

        talkItems.forEach(item => {
            const year = item.getAttribute('data-year');
            const text = item.textContent.toLowerCase();

            const yearMatch = !yearValue || year === yearValue;
            const searchMatch = !searchValue || text.includes(searchValue);

            if (yearMatch && searchMatch) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        });
    }

    function exportBibTeX() {
        alert('BibTeX export functionality will be implemented with backend support.');
    }
});
