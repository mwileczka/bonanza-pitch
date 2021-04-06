 function DealCards(){
            AddCardToHand('AS');
            AddCardToHand('KS');
            AddCardToHand('QS');
            AddCardToHand('JS');
            AddCardToHand('10S');
            AddCardToHand('5D');
        }
function AddCardToHand(card){
    var container = document.getElementById("divHand");
    var img = document.createElement("img");
    img.setAttribute("src", "../static/cards/" + card + ".svg")
    img.setAttribute("class", "card")
    container.appendChild(img);
}