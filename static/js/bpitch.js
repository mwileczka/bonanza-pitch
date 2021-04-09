function DealCards(){
    RefreshPlayerDisplays();

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
SetBidTurn(1,5);
    // SetPlayCard("3C", "playedCardTop");
    // SetPlayCard("4C", "playedCardBottom");
    //  SetPlayCard("5C", "playedCardLeft");
    //  SetPlayCard("6C", "playedCardRight");
}
function StartGame(){

}

function RefreshPlayerDisplays(){
    $( "#playerNameSouth" ).html(username + " &#8226 " + theBid);
}

function SetBidTurn(playerID, minBid) {
    if (playerID === -1) {
        $( "#divBid" ).hide();
    }else if (playerID === 1){
        $( "#divBid" ).show();
        $( "#bidStatusMessage" ).html("It's your turn to bid...");
        SetBidOptions(minBid);
    }else
    {
        $( "#divBid" ).show();
        $( "#bidStatusMessage" ).html("Waiting for Player " + playerID + " to bid...");
    }

    SetBidOptions(5);
}
function SetBidOptions(minBid){
    var options = document.getElementById("bidOptions");
    options.innerHTML="";
    var tbl = document.createElement("table");
    tbl.setAttribute("style","width:100%;")
    options.appendChild(tbl);

    var i = 0;
    var j = 0;
    //6 rows of 3
    for (i = 0 ; i <= 5; i++)
    {
        var tr = document.createElement("tr");
        tr.setAttribute("style","width:100%;")
        tbl.appendChild(tr);
        for (j = 0; j <=2; j++) {
            var td = document.createElement("td");
            var bid = (i*3) + j + 1;
            var btn = CreateBidButton(bid, (bid >= minBid), bid);
            td.appendChild(btn);
            tr.appendChild(td);
        }
    }
    //shoot the moon and pass
    var row = document.createElement("tr");
    row.setAttribute("style","width:100%;")
    tbl.appendChild(row);
    var tdMoon = document.createElement("td");
    tdMoon.setAttribute("colspan","2")
    row.appendChild(tdMoon);
    var btnMoon = CreateBidButton("Shoot the Moon", true, 19);
    tdMoon.appendChild(btnMoon);
    var tdPass = document.createElement("td");
    row.appendChild(tdPass);
    var btnPass = CreateBidButton("Pass", true, 0);
    tdPass.appendChild(btnPass);

}
function CreateBidButton(txt, enabled, val){
    var btn = document.createElement("button");
    btn.setAttribute("type", "button");
    btn.setAttribute("style", "width:100%;font-size:2vh");
    if (enabled){
        btn.setAttribute("class", "btn btn-primary");
        btn.setAttribute("data-dismiss", "modal");
        btn.onclick=function(){SendBid(val);};
    }else{
        btn.setAttribute("class", "btn btn-primary disabled");
    }
    btn.innerHTML = txt;
    return btn;
}
var theBid =0;
function SendBid(bid){

    $( "#divBid" ).hide();
    var strBid = "bid:" + bid;
    socket.emit(strBid);
    theBid = bid;
    RefreshPlayerDisplays();

     $( "#divSelectSuit" ).show();

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

