console.log("ajax trigger")
let submit_action = document.getElementById("submit_button")
console.log(submit_action)
// submit_action.addEventListener('click', submitclickevent)

function wait_hour() {
    console.log('click event function trigger');
    try{
       let ajax = new XMLHttpRequest();
    //    var spin=document.getElementById("loader-sp-6");
    //    spin.classList.remove("loader-spin-off")
    //    spin.classList.add("loader-spin-on")
       ajax.onreadystatechange = function(){
       if (this.readyState === 4){
           if (this.status === 200) {
               console.log("page loaded")
            //  spin.classList.remove("loader-spin-on")
            //  spin.classList.add("loader-spin-off")
            //    document.getElementById("exa_data_button").innerHTML = this.responseText;
               //console.log(this.responseText)
           }
       }
   }
   ajax.open("GET", "{% url 'submit_form' %}", true);
   }
   catch (e){
     console.log(e);
   }
   }


