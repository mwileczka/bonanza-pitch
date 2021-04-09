var tableState = {theBid: 0, trump:'', dealer:0, lead:0,
    seats:[
        {hand:6, played:'',bid:-1,dealer:true,lead:false,username:'Laura'},
        {hand:6, played:'',bid:-1,dealer:false,lead:false,username:'Teddy'},
        {hand:6, played:'',bid:-1,dealer:false,lead:false,username:'Ben'},
        {hand:6, played:'',bid:-1,dealer:false,lead:false,username:'Mike'}
    ]
    , score:[0,0], points:[0,0], deck_ct:0};

function StartGame(){
    RefreshTable(tableState);
}
function RefreshTable(state){
    //South Seat
    RefreshPlayerDisplay(state.seats[0],'playerNameSouth');
    //West Seat
    DealHand('divHandWest', state.seats[1].hand);
    RefreshPlayerDisplay(state.seats[1],'playerNameWest');
    //North Seat
    DealHand('divHandNorth', state.seats[2].hand);
    RefreshPlayerDisplay(state.seats[2],'playerNameNorth');
    //East Seat
    DealHand('divHandEast', state.seats[3].hand);
    RefreshPlayerDisplay(state.seats[3],'playerNameEast');

}
function DealHand(handName, ct){
    var hand = document.getElementById(handName);
    if(hand.childElementCount !== ct){
        hand.innerHTML= "";
        var i = 0;
        for (i = 0 ; i < ct ;i++){
            AddCardToHand('RED_BACK', handName);
        }
    }
}

function RefreshPlayerDisplay(seat, displayName){
    var str = seat.username
    if (seat.bid === 0){
        str +=+" &bull; Pass";
    }
    else if (seat.bid > 0){
        str += " &bull; " + seat.bid;
    }
    if (tableState.trump === 'S') str += " &bull; &spadesuit;"
    else if (tableState.trump === 'D') str += " &bull; &diams;"
    else if (tableState.trump === 'C') str += " &bull; &clubsuit;"
    else if (tableState.trump === 'H') str += " &bull; &heartsuit;"

    $( "#"+displayName ).html(str);
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

function SendBid(bid){

    $( "#divBid" ).hide();
    var strBid = "bid:" + bid;
    socket.emit(strBid);
    tableState.theBid = bid;
    RefreshPlayerDisplays();

}
function OnSelectSuit(suit){
    socket.emit("suit:" + suit);
    tableState.trump = suit;
    RefreshPlayerDisplays();
    $( "#divSelectSuit" ).hide();
}
function ShowSelectSuit(){
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

