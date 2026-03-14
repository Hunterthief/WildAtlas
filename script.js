let animals=[]

fetch("data/animals.json")
.then(r=>r.json())
.then(data=>{

animals=data

render(data)

})

function render(list){

const grid=document.getElementById("grid")

grid.innerHTML=""

list.forEach(a=>{

const card=document.createElement("div")

card.className="card"

card.innerHTML=`
<img loading="lazy" src="${a.image}">
<h3>${a.name}</h3>
<p>${a.description || ""}</p>
`

card.onclick=()=>{

location.href=`animal.html?name=${encodeURIComponent(a.name)}`

}

grid.appendChild(card)

})

}

const search=document.getElementById("search")

search.addEventListener("input",e=>{

const q=e.target.value.toLowerCase()

render(
animals.filter(a=>a.name.toLowerCase().includes(q))
)

})
