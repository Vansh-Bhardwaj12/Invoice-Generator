const counters=document.querySelectorAll("h1");

counters.forEach(counter=>{

let start=0;

const end=parseInt(counter.innerText);

const speed=20;

const update=()=>{

start+=Math.ceil(end/50);

if(start<end){

counter.innerText=start;

setTimeout(update,speed);

}

else{

counter.innerText=end;

}

};

update();

});