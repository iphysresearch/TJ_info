// Table sorting and filtering functionality
document.addEventListener('DOMContentLoaded', function() {
    const table = document.getElementById('publications-table');

    if (table) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(table.querySelectorAll('tbody tr'));

        // Sorting functionality
        const headers = table.querySelectorAll('th[data-sort]');
        headers.forEach(header => {
            header.addEventListener('click', function() {
                const sortKey = this.getAttribute('data-sort');
                sortTable(sortKey);
            });
        });

        function sortTable(sortKey) {
            const visibleRows = rows.filter(r => r.style.display !== 'none');

            visibleRows.sort((a, b) => {
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

            visibleRows.forEach(row => tbody.appendChild(row));
            applyZebraStripes();
        }

        // Apply zebra stripes to visible rows
        function applyZebraStripes() {
            const visibleRows = rows.filter(r => r.style.display !== 'none');
            visibleRows.forEach((row, index) => {
                row.classList.toggle('row-even', index % 2 === 1);
            });
        }

        // Paper filter (Taiji vs All)
        const filterRadios = document.querySelectorAll('input[name="paper-filter"]');

        function applyFilter(filterValue) {
            rows.forEach(row => {
                if (filterValue === 'taiji') {
                    row.style.display = row.getAttribute('data-taiji') === 'true' ? '' : 'none';
                } else {
                    row.style.display = '';
                }
            });
            applyZebraStripes();
        }

        // Apply default filter (taiji only)
        applyFilter('taiji');

        filterRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                applyFilter(this.value);
            });
        });
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
