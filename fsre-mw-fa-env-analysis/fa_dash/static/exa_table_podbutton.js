function db_art_method(dart_url,exa,db_name,pod_size,pod, method='post') {
// db_art_method('{{ exa.dart_url }}','{{ exa.exa }}','{{ exa.db_name }}','{{ exa.pod_size }}','{{ pod }}')">
  //below code will add hidden form with two key/values (1-> dart_rul , 2-> csrf token for post method)
  console.log(dart_url,exa,db_name,pod_size,pod)
  const path = 'db_dash/'
  const form = document.createElement("form")
  form.method = method;
  form.action = path;
  
    const hiddenField = document.createElement('input');
  hiddenField.type = 'hidden';
  hiddenField.name = "dart_url";
  hiddenField.value = dart_url;
    form.appendChild(hiddenField);

    const hiddenField_1 = document.createElement('input');
  hiddenField_1.type = 'hidden';
  hiddenField_1.name = "exa_node";
  hiddenField_1.value = exa;
  form.appendChild(hiddenField_1);

  const hiddenField_2 = document.createElement('input');
  hiddenField_2.type = 'hidden';
  hiddenField_2.name = "pod_name";
  hiddenField_2.value = pod;
    form.appendChild(hiddenField_2);
  
  const hiddenField_3 = document.createElement('input');
  hiddenField_3.type = 'hidden';
  hiddenField_3.name = "db_name";
  hiddenField_3.value = db_name;
  form.appendChild(hiddenField_3);

  const hiddenField_4 = document.createElement('input');
  hiddenField_4.type = 'hidden';
  hiddenField_4.name = "pod_size";
  hiddenField_4.value = pod_size;
  form.appendChild(hiddenField_4);
  
  const hiddenField_5 = document.createElement('input');
  hiddenField_5.type = 'hidden';
  hiddenField_5.name = "csrfmiddlewaretoken";
  hiddenField_5.value = csrftoken;
    form.appendChild(hiddenField_5);
    
    
    document.body.appendChild(form);
  form.submit();
}
  

document.getElementById("submit_button").style.pointerEvents='none';

// const td_length = document.getElementsByClassName("pod_name").length 
// console.log(td_length)

// var csrftoken = '{{ csrf_token }}';

// function db_art_method(dart_url) {
//     console.log("inside db_art_method ")
//     let ajax = new XMLHttpRequest();
//     ajax.open("POST", db_dash, true);
//     ajax.setRequestHeader("X-CSRFToken", csrftoken);
//     const data = new FormData();
//     data.append('dart_url', dart_url);
//     ajax.send(data);
// }


// document.getElementsByClassName("dart_url")[0].hidden = 'True'
// let dart_json={'dart_url':''}
// const dart_length = document.getElementsByClassName("dart_url").length
// console.log(dart_length)
// for (let i = 0; i < dart_length; i++) {
//     console.log("loop triggered")
//     document.getElementsByClassName("dart_url")[i].hidden = 'True'
//     darturl = document.getElementsByClassName("dart_url")[0].innerText.trim()
//     console.log(darturl)
// }

// for (let i = 0; i < td_length; i++) {
//     console.log(document.getElementsByClassName("pod_name")[i].addEventListener('click',testpage))
// }

// function testpage() {
//     window.location = "/db_dash/"
//     // const request = new XMLHttpRequest();
//     // request.open("GET", "/db_dash/",true);
//     // request.send();

// }


// /**
//  * sends a request to the specified url from a form. this will change the window location.
//  * @param {string} path the path to send the post request to
//  * @param {object} params the parameters to add to the url
//  * @param {string} [method=post] the method to use on the form
//  */
// function post(path, params, method='post') {

//   // The rest of this code assumes you are not using a library.
//   // It can be made less verbose if you use one.
//   const form = document.createElement('form');
//   form.method = method;
//   form.action = path;

//   for (const key in params) {
//     if (params.hasOwnProperty(key)) {
//       const hiddenField = document.createElement('input');
//       hiddenField.type = 'hidden';
//       hiddenField.name = key;
//       hiddenField.value = params[key];

//       form.appendChild(hiddenField);
//     }
//   }

//   document.body.appendChild(form);
//   form.submit();
// }
// post('/contact/', {name: 'Johnny Bravo'});   