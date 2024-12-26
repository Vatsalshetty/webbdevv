const container = document.getElementById('container');
const registerBtn = document.getElementById('register');
const loginBtn = document.getElementById('login');

// Toggle classes for animations
registerBtn.addEventListener('click', () => {
    container.classList.add("active");
});

loginBtn.addEventListener('click', () => {
    container.classList.remove("active");
});

// Add form submission handling
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', (event) => {
        event.preventDefault(); // Prevent page reload
        const formData = new FormData(form);
        console.log(Object.fromEntries(formData)); // Placeholder: Replace with actual backend logic
        alert('Form submitted successfully!');
    });
});
