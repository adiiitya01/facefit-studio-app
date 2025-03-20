document.querySelector('.login').onclick=()=> {
   
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
 
    if (username.value === "user" && password.value==="12345678"){
        window.location.href = "index.html";
    }
    else{
        username.style.border = "2px solid red";
        password.style.border = "2px solid red";
    }

};