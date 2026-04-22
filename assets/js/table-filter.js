// Table sorting and talks filtering functionality
document.addEventListener('DOMContentLoaded', function() {
    const table = document.getElementById('publications-table');

    if (table) {
        const rows = table.querySelectorAll('tbody tr');

        // Sorting functionality
        const headers = table.querySelectorAll('th[data-sort]');
        headers.forEach(header => {
            header.addEventListener('click', function() {
                const sortKey = this.getAttribute('data-sort');
                sortTable(sortKey);
            });
        });

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
    }
});
