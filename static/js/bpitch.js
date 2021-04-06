 function DealCards(){
            AddCardToHand('AS', 'divHand');
            AddCardToHand('KS', 'divHand');
            AddCardToHand('QS', 'divHand');
            AddCardToHand('JS', 'divHand');
            AddCardToHand('10S', 'divHand');
            AddCardToHand('5D', 'divHand');

            var i;
            for (i = 0 ; i < 6 ; i++){
                AddCardToHand('RED_BACK', 'divHandTop');
            }
            for (i = 0 ; i < 6 ; i++){
                AddCardToHand('RED_BACK', 'divHandLeft');
            }
            for (i = 0 ; i < 6 ; i++){
                AddCardToHand('RED_BACK', 'divHandRight');
            }

            SetPlayCard("3C", "playedCardTop");
            SetPlayCard("4C", "playedCardBottom");
             SetPlayCard("5C", "playedCardLeft");
             SetPlayCard("6C", "playedCardRight");
        }
function AddCardToHand(card, hand){
    var container = document.getElementById(hand);
    var img = document.createElement("img");
    img.setAttribute("src", "../static/cards/" + card + ".svg")
    img.setAttribute("class", "pcard")
    container.appendChild(img);
}
function SetPlayCard(card, elem){
    var container = document.getElementById(elem);
    var img = document.createElement("img");
    img.setAttribute("src", "../static/cards/" + card + ".svg")
    img.setAttribute("class", "pcard")
    container.innerHTML = "";
    container.appendChild(img);
}

function HandleChatClick(){
    var chat = document.getElementById("divChat");
    var gameTable = document.getElementById("gameTable");

    if (chat.style.display ==="none"){
        chat.style.display = "block";
        gameTable.style.display = "none";
    } else{
        chat.style.display = "none";
        gameTable.style.display = "block";
    }


}

