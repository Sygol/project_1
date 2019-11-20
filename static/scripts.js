
// Function to check Whether both passwords
// is same or not.
function checkPassword(form) {
    password1 = form.password1.value;
    password2 = form.password2.value;

    if (password1 != password2) {
        document.querySelector("#password__alert").style.display="block"
        return false;
    }

    else{
        return true;
    }
}
