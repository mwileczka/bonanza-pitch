 function DealCards(){
            AddCardToHand('AS', 'divHand');
            AddCardToHand('KS', 'divHand');
            AddCardToHand('QS', 'divHand');
            AddCardToHand('JS', 'divHand');
            AddCardToHand('10S', 'divHand');
            AddCardToHand('5D', 'divHand');

            AddCardToHand('RED_BACK', 'divHandTop');
            AddCardToHand('RED_BACK', 'divHandTop');
            AddCardToHand('RED_BACK', 'divHandTop');
            AddCardToHand('RED_BACK', 'divHandTop');
            AddCardToHand('RED_BACK', 'divHandTop');
            AddCardToHand('RED_BACK', 'divHandTop');
        }
function AddCardToHand(card, hand){
    var container = document.getElementById(hand);
    var img = document.createElement("img");
    img.setAttribute("src", "../static/cards/" + card + ".svg")
    img.setAttribute("class", "pcard")
    container.appendChild(img);
}