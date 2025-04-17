document.getElementById("uploadForm").addEventListener("submit", function(event) {
    event.preventDefault();

    let fileInput = document.getElementById("fileInput");
    let formData = new FormData();
    formData.append("file", fileInput.files[0]);

    fetch("/monument", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById("monumentName").innerText = data.monument_type;
        document.getElementById("coordinates").innerText = data.coordinates;
    })
    .catch(error => console.error("Error:", error));

document.addEventListener("DOMContentLoaded", function () {
    // Signup Validation
    const signupForm = document.getElementById("signup-form");
    if (signupForm) {
        signupForm.addEventListener("submit", function (event) {
            event.preventDefault(); // Prevent form submission
            const username = document.getElementById("username").value.trim();
            const password = document.getElementById("password").value;
            const confirmPassword = document.getElementById("confirm-password").value;
            const errorDiv = document.getElementById("signup-error");
            const successDiv = document.getElementById("signup-success");

            let errorMessage = "";

            // Password validation
            const passwordRegex = /^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
            if (username.includes(" ") || password.includes(" ")) {
                errorMessage = "❌ Spaces are not allowed in username or password.";
            } else if (/^\d/.test(username)) {
                errorMessage = "❌ Username cannot start with a number.";
            } else if (username.length < 3) {
                errorMessage = "❌ Username must be at least 3 characters long.";
            } else if (!passwordRegex.test(password)) {
                errorMessage = "❌ Password must be at least 8 characters long and include at least 1 uppercase letter, 1 number, and 1 special character.";
            } else if (password !== confirmPassword) {
                errorMessage = "❌ Passwords do not match.";
            } else {
                // Check if username already exists
                fetch("/check_username", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ username: username })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.exists) {
                        errorDiv.innerHTML = "❌ Username already exists.";
                    } else {
                        // If no errors, submit the form via AJAX
                        fetch("/signup", {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/x-www-form-urlencoded"
                            },
                            body: new URLSearchParams({
                                username: username,
                                password: password
                            })
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.message) {
                                successDiv.innerHTML = "✅ " + data.message;
                                successDiv.classList.remove("hidden");
                                setTimeout(() => {
                                    window.location.href = "/login"; // Redirect to login after 10 seconds
                                }, 10000); // 10 seconds
                            } else if (data.error) {
                                errorDiv.innerHTML = "❌ " + data.error;
                            }
                        });
                    }
                });
            }

            if (errorMessage) {
                errorDiv.innerHTML = errorMessage;
                successDiv.classList.add("hidden"); // Hide success message if there's an error
            }
        });
    }
});
    // Login Validation
    const loginForm = document.getElementById("login-form");
    if (loginForm) {
        loginForm.addEventListener("submit", function (event) {
            event.preventDefault(); // Prevent form submission
            const username = document.getElementById("login-username").value.trim();
            const password = document.getElementById("login-password").value;
            const errorDiv = document.getElementById("login-error");

            // Check if username starts with a number
            if (/^\d/.test(username)) {
                errorDiv.innerHTML = "❌ Username cannot start with a number.";
                return; // Exit the function if the username is invalid
            }

            if (username === "" || password === "") {
                errorDiv.innerHTML = "❌ Username and Password cannot be empty.";
            } else {
                // Make an AJAX request to validate login
                fetch("/login", {
                    method: "POST",
                    body: new FormData(loginForm),
                })
                .then(response => response.text())
                .then(data => {
                    if (data.includes("Invalid credentials!")) {
                        errorDiv.innerHTML = "❌ Incorrect Username or Password.";
                    } else {
                        window.location.href = "/dashboard"; // Redirect if successful
                    }
                })
                .catch(error => {
                    errorDiv.innerHTML = "❌ An error occurred. Please try again.";
                });
            }
        });
    }
});