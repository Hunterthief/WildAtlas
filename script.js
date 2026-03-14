let animals=[]

fetch("data/animals.json")
.then(r=>r.json())
.then(data=>{

animals=data

renderGrid()

populateCompare()

})

function renderGrid(){

const grid=document.getElementById("grid")

if(!grid) return

animals.forEach(a=>{

const card=document.createElement("div")
card.className="card"

card.innerHTML=`
<img loading="lazy" src="${a.image}">
<h3>${a.name}</h3>
`

card.onclick=()=>{

location.href=`animal.html?name=${encodeURIComponent(a.name)}`

}

grid.appendChild(card)

})

}

const search=document.getElementById("search")

if(search){

search.addEventListener("input",e=>{

const q=e.target.value.toLowerCase()

const filtered=animals.filter(a=>a.name.toLowerCase().includes(q))

document.getElementById("grid").innerHTML=""

filtered.forEach(a=>{

const card=document.createElement("div")

card.className="card"

card.innerHTML=`
<img loading="lazy" src="${a.image}">
<h3>${a.name}</h3>
`

card.onclick=()=>location.href=`animal.html?name=${encodeURIComponent(a.name)}`

document.getElementById("grid").appendChild(card)

})

})

}

function populateCompare(){

const aSel=document.getElementById("a")
const bSel=document.getElementById("b")

if(!aSel) return

animals.forEach(an=>{

let o1=document.createElement("option")
o1.value=an.name
o1.textContent=an.name

let o2=o1.cloneNode(true)

aSel.appendChild(o1)
bSel.appendChild(o2)

})

}

function compare(){

const a=document.getElementById("a").value
const b=document.getElementById("b").value

const A=animals.find(x=>x.name===a)
const B=animals.find(x=>x.name===b)

document.getElementById("result").innerHTML=`

<table>

<tr>
<th></th>
<th>${A.name}</th>
<th>${B.name}</th>
</tr>

<tr>
<td>Category</td>
<td>${A.category}</td>
<td>${B.category}</td>
</tr>

<tr>
<td>Habitat</td>
<td>${A.habitat}</td>
<td>${B.habitat}</td>
</tr>

<tr>
<td>Diet</td>
<td>${A.diet}</td>
<td>${B.diet}</td>
</tr>

<tr>
<td>Size</td>
<td>${A.size}</td>
<td>${B.size}</td>
</tr>

<tr>
<td>Weight</td>
<td>${A.weight}</td>
<td>${B.weight}</td>
</tr>

</table>

`

}
