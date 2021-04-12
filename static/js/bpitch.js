var tableState = {theBid: 0, trump:'', dealer:0, lead:0,
    seats:[
        {hand:6, played:'',bid:-1,dealer:true,lead:false,username:'Laura'},
        {hand:6, played:'',bid:-1,dealer:false,lead:false,username:'Teddy'},
        {hand:6, played:'',bid:-1,dealer:false,lead:false,username:'Ben'},
        {hand:6, played:'',bid:-1,dealer:false,lead:false,username:'Mike'}
    ]
    , score:[0,0], points:[0,0], deck_cnt:0, kitty_cnt:0};

function StartGame(){
    //RefreshTable(tableState);
//OnRequestBid(0);
   // OnRequestSuit();
}
function RefreshTable(state){
    var westSeat = seat+1;
    var northSeat = seat+2;
    var eastSeat = seat+3;

    if (westSeat>3) westSeat -=4;
    if (northSeat>3) northSeat -=4;
    if (eastSeat>3) eastSeat -=4;

    //South Seat
    RefreshPlayerDisplay(state.seats[seat],'playerNameSouth');
    //West Seat
    DealHiddenHand('divHandWest', state.seats[westSeat].hand);
    RefreshPlayerDisplay(state.seats[westSeat],'playerNameWest');
    //North Seat
    DealHiddenHand('divHandNorth', state.seats[northSeat].hand);
    RefreshPlayerDisplay(state.seats[northSeat],'playerNameNorth');
    //East Seat
    DealHiddenHand('divHandEast', state.seats[eastSeat].hand);
    RefreshPlayerDisplay(state.seats[eastSeat],'playerNameEast');

    RefreshKitty(state.kitty_cnt);

    if (state.turn !== seat)
        $('#divMessage').html('Waiting for ' + state.seats[state.turn].name);
    else
        $('#divMessage').html("");

}
function OnRequestBid(req_bid){
    SetBidOptions(req_bid.min, req_bid.max);
    $('#divMessage').html("Your turn to bid")
     $('#divBid').show();
}
function OnRequestSuit(data){
    $( "#divSelectSuit" ).show();
}

function RefreshKitty(ct){
    var k = document.getElementById('divKitty');
    if (k.childElementCount !== ct) {
        k.innerHTML = "";
        var i = 0;
        for (i = 0; i < ct; i++) {
            AddCardToHand('RED_BACK', 'divKitty');
        }
    }
}

function DealHand(hand){
    var h = document.getElementById('divHandSouth');
    h.innerHTML= "";

    var i = 0;
    for (i = 0 ; i < hand.cards.length ;i++) {
        AddCardToHand(hand.cards[i], 'divHandSouth');
    }
}

function DealHiddenHand(handName, ct){
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
    var str = '';
    if (seat.name !== null) str += seat.name;

    if (seat.bid === 0){
        str += " &bull; Pass";
    }
    else if (seat.bid !== null && seat.bid > 0){
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
function SetBidOptions(minBid, maxBid){
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
            var btn = CreateBidButton(bid, (bid >= minBid && bid <= maxBid), bid);
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
    var btnMoon = CreateBidButton("Shoot the Moon", (maxBid >= 19), 19);
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
    socket.emit('bid', bid);
}
function OnSelectSuit(suit){
    socket.emit('suit', suit);
    tableState.trump = suit;
    $( "#divSelectSuit" ).hide();
}
function AddCardToHand(card, hand){
    var container = document.getElementById(hand);
    var img = document.createElement("img");
    img.setAttribute("src", "../static/cards/" + card + ".svg")
    img.setAttribute("class", "pcard")
    img.onclick = function(){OnCardClick(card, hand);};
    container.appendChild(img);
}
function OnCardClick(theCard, hand){
    if (hand==='divHandSouth'){
        socket.emit('play', {card: theCard});
    }
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

