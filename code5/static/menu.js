document.addEventListener('DOMContentLoaded', () => {
    const vegToggle = document.getElementById('veg-toggle');
    const menuItems = document.querySelectorAll('.menu-item');

    vegToggle.addEventListener('change', () => {
        const showVegOnly = vegToggle.checked;

        menuItems.forEach(item => {
            const isVeg = item.getAttribute('data-veg') === "true";
            if (showVegOnly && !isVeg) {
                item.style.display = 'none'; // Hide non-veg items
            } else {
                item.style.display = ''; // Show all items
            }
        });
    });
});
