var tableState = {};

function StartGame(){
    //window.location.reload(true);
    //RefreshTable(tableState);
//OnRequestBid(0);
    //OnRequestSuit();
}
function GetSeatNum(NSEW){
    var tmp = 0;
    if (NSEW === 'S')
        return seat;
    else if (NSEW === 'W')
        tmp = seat + 1;
    else if (NSEW === 'N')
        tmp = seat + 2;
    else if (NSEW === 'E')
        tmp = seat + 3;

    if (tmp > 3) tmp -=4;
    return tmp
}
function RefreshTable(state){
    tableState = state;

    var westSeat = GetSeatNum('W');
    var northSeat = GetSeatNum('N');
    var eastSeat = GetSeatNum('E');

    var s = 0;
    var okToShowPlay = false;
    for (s = 0 ; s<=3 ; s++){
        if (state.seats[s].played !== null){okToShowPlay = true;}

    }

    if (okToShowPlay){$( "#tblPlay" ).show();}else{$( "#tblPlay" ).hide();}


    //South Seat
    RefreshPlayerDisplay(seat,'South');
    //West Seat
    DealHiddenHand('divHandWest', state.seats[westSeat].hand);
    RefreshPlayerDisplay(westSeat,'West');
    //North Seat
    DealHiddenHand('divHandNorth', state.seats[northSeat].hand);
    RefreshPlayerDisplay(northSeat,'North');
    //East Seat
    DealHiddenHand('divHandEast', state.seats[eastSeat].hand);
    RefreshPlayerDisplay(eastSeat,'East');

    RefreshKitty(state.kitty_cnt);

    if (state.turn !== seat)
        $('#divMessage').html('Waiting for ' + state.seats[state.turn].name);
    else
        $('#divMessage').html("");
    RefreshScore();
}
function RefreshScore(){
    var str = '';
    if (tableState.seats[0].name !== null && tableState.seats[1].name !== null && tableState.seats[2].name !== null && tableState.seats[3].name !== null)
    {
        var tbl= document.getElementById("tblCardScore");
    removeAllChildNodes(tbl);

    var tr1 = document.createElement("tr");
    tbl.appendChild(tr1);
    var th = document.createElement("th");
    th.setAttribute("style", "border-bottom: 1px solid white;width:50%;")
    if (seat === 0 || seat === 2)
        th.innerHTML = "Us";
    else
        th.innerHTML = "Them";
        //th.innerHTML = tableState.seats[0].name + " & " + tableState.seats[2].name;
    tr1.appendChild(th);

    th = document.createElement("th");
    //th.innerHTML = tableState.seats[1].name + " & " + tableState.seats[3].name;
    if (seat === 1 || seat === 3)
        th.innerHTML = "Us";
    else
        th.innerHTML = "Them";
    th.setAttribute("style", "border-bottom: 1px solid white; border-left: 1px solid white;width:50%;")
    tr1.appendChild(th);


        var tr = document.createElement("tr");
        tbl.appendChild(tr);
        var td = document.createElement("td");
        td.innerHTML = tableState.teams[0].score;
        tr.appendChild(td);
        td = document.createElement("td");
        td.innerHTML = tableState.teams[1].score;
        td.setAttribute("style", "border-left: 1px solid white;")
        tr.appendChild(td);

        //point cards
        tr = document.createElement("tr");
        tbl.appendChild(tr);
        for (i=0;i < tableState.teams.length ; i++)
        {
            td = document.createElement("td");
            td.setAttribute("style", "font-size:1.5vh;")
            str = "";
            for (j=0 ; j< tableState.teams[i].cards_won.length ; j++){
                var c = tableState.teams[i].cards_won[j];
                var suit = c.slice(1,2);
                if (suit === tableState.trump)
                    str += GetCardHTML(c, true) + " ";
            }

            td.innerHTML = str.trim();
            if (i === 1) {td.setAttribute("style", "border-left: 1px solid white;font-size:1.5vh;");}
            tr.appendChild(td);
        }

       $('#divScoreCard').show();
    }
    else {
        $('#divScoreCard').hide();
    }
}
function removeAllChildNodes(parent) {
    while (parent.firstChild) {
        parent.removeChild(parent.firstChild);
    }
}
function OnRequestBid(req_bid){
    SetBidOptions(req_bid.min, req_bid.max);
    $('#divMessage').html("Your turn to bid");
     $('#divBid').show();
}
function OnRequestSuit(data){
    $('#divMessage').html();
    $( "#divSelectSuit" ).show();
}
function OnRequestDeal(data){
    RefreshEndOfHandScore(data)
    $( "#divHandSummary" ).show();
}
var discardMode = false;
function OnRequestDiscard(data){
    if (data.cnt > 0) {
        discardMode = true;
        var msg = "Discard " + data.cnt + " card";
        if (data.cnt > 1){msg += "s";}
        $('#divMessage').html(msg);

         var hand = tableState.seats[seat].hand;
         for (var i = 0 ; i < hand.length ; i++){
            var img = document.getElementById("card_" + hand[i]);
            img.classList.add("playableCard");
         }
    }
}
var PlayableCards = [];
function OnRequestPlay(data){
    PlayableCards = data;
    var i = 0;
    for (i = 0 ; i < data.length ; i++){
        var img = document.getElementById("card_" + data[i]);
        img.classList.add("playableCard");
    }
    $('#divMessage').html("It's your turn");
}
function Deal(){
    socket.emit('deal',{});
    $( '#divHandSummary' ).hide();
}

function RefreshEndOfHandScore(data){
    var str = '';var i = 0;var j = 0;var tr;var td;var str;
    if (tableState.seats[0].name !== null && tableState.seats[1].name !== null && tableState.seats[2].name !== null && tableState.seats[3].name !== null) {

        //headings
        var tbl= document.getElementById("divHandSummaryContent");
        removeAllChildNodes(tbl);

        tr = document.createElement("tr");
        tr.setAttribute("style", "font-size: 2vh;")
        tbl.appendChild(tr);

        var th = document.createElement("th");
        th.setAttribute("class", "hand-summary-left")
        if (seat === 0 || seat === 2)
            th.innerHTML = "Us";
        else
            th.innerHTML = "Them";

        //th.innerHTML = tableState.seats[0].name + " & " + tableState.seats[2].name;
        tr.appendChild(th);

        th = document.createElement("th");
        if (seat === 1 || seat === 3)
            th.innerHTML = "Us";
        else
            th.innerHTML = "Them";
        //th.innerHTML = tableState.seats[1].name + " & " + tableState.seats[3].name;
        th.setAttribute("class", "hand-summary-right")
        tr.appendChild(th);

        //scores
        for (i = 0 ; i< data.scores.length ; i++){
            var isLastScore = false;
            var style = "";
            var spanStyle0 = "";
            var spanStyle1 = "";
            if (i !== data.scores.length - 1){ style += "hand-summary-old-score "}
            else{
                if (data.game_winner === 1){spanStyle1 += 'hand-summary-winner ';}
                else if (data.game_winner === 0){spanStyle0 = 'hand-summary-winner ';}
            }

            tr = document.createElement("tr");
            tr.setAttribute("class", "hand-summary ")
            tbl.appendChild(tr);
            td = document.createElement("td");
            td.setAttribute("class", style + spanStyle0)

            td.innerHTML = data.scores[i][0];
            tr.appendChild(td);

            td = document.createElement("td");
            td.innerHTML = data.scores[i][1];

            style += "hand-summary-right ";
            td.setAttribute("class", style + spanStyle1)
            tr.appendChild(td);
        }

         //point cards
        tr = document.createElement("tr");
        tr.setAttribute("style", "font-size: 1.5vh;")
        tbl.appendChild(tr);
        for (i=0;i < data.point_cards.length ; i++)
        {
            td = document.createElement("td");
            str = "";
            for (j=0 ; j< data.point_cards[i].length ; j++){
                str += GetCardHTML(data.point_cards[i][j]) + " ";
            }

            td.innerHTML = str.trim();
            if (i === 1) {td.setAttribute("class", "hand-summary-point-cards-right ");}
            else {td.setAttribute("class", "hand-summary-point-cards-left ");}
            tr.appendChild(td);
        }
        var divLeftInDeck= document.getElementById("divLeftInDeck");

        if (data.deck_trump.length === 0)
        {
            divLeftInDeck.innerHTML= "No trump left in deck"
        }
        else
        {
            divLeftInDeck.innerHTML = "Trump in Deck: "
            for (i = 0 ; i < data.deck_trump.length ; i++)
            {
               divLeftInDeck.innerHTML += GetCardHTML(data.deck_trump[i] + " ");
            }
        }

        $('#divScoreCard').show();
    }else{
        $('#divScoreCard').hide();
    }
}
function GetCardHTML(card, useWhiteForBlack){
    var str = card.slice(0, 1);
    var suit = card.slice(1,2);

    if (str === 'T') {str ='10';}
    str += GetSuitHTML(suit, useWhiteForBlack);

    return str;
}
function GetSuitHTML(suit, useWhiteForBlack){
    var blackColor = "black";
    if (useWhiteForBlack)
        blackColor = "white";
    if (suit === 'S')
        return "<span style='color:" + blackColor +";'>" + "&spadesuit;" + "</span>";
    else if (suit === 'D')
        return "<span style='color:red;'>" + "&diams;" + "</span>";
    else if (suit === 'C')
        return "<span style='color:" + blackColor + ";'>" + "&clubsuit;" + "</span>";
    else if (suit === 'H')
        return "<span style='color:red;'>" + "&heartsuit;" + "</span>";

    return '';
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

function OnKick(NSEW){
    var seatNum = GetSeatNum(NSEW);
    socket.emit('kick', seatNum);
}


function RefreshPlayerDisplay(seatNum, NSEW){
    var seat = tableState.seats[seatNum];
    var str = '';
    if (seat.name === null){
        $( "#kick" + NSEW ).hide();
    }else{
        str += seat.name;
        $( "#kick" + NSEW ).show();
    }

    $( "#playerName" + NSEW ).html(str);
    str = '';
    if(seatNum === tableState.dealer){str += "Dealer<br/>"}
    if (seat.bid === 0 && tableState.trump === null){
        str += "Pass";
    }
    else if (seat.bid !== null && seat.bid > 0){
        str += "Bid: " + seat.bid;
    }

    if (tableState.bidder === seatNum){
        str+= GetSuitHTML(tableState.trump, true);
    }
    var grayed = false;
    if (tableState.winner !== null && tableState.winner !== seatNum)
    {
        grayed = true;
    }

    SetPlayCard(seat.played, 'playedCard' + NSEW, grayed);

    $( "#playerStats" + NSEW ).html(str);

}

function SetBidOptions(minBid, maxBid){
    var options = document.getElementById("bidOptions");
    options.innerHTML="";
    var tbl = document.createElement("table");
    tbl.setAttribute("style","width:100%;")
    options.appendChild(tbl);

    var i = 0;
    var j = 0;
    //3 rows of 6
    for (i = 0 ; i <= 2; i++)
    {
        var tr = document.createElement("tr");
        tr.setAttribute("style","width:100%;")
        tbl.appendChild(tr);
        for (j = 0; j <=5; j++) {
            var td = document.createElement("td");
            var bid = (i*6) + j + 1;
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
    $('#divMessage').html("");
}
function OnSelectSuit(suit){
    socket.emit('suit', suit);
    tableState.trump = suit;
    $( "#divSelectSuit" ).hide();
}
function AddCardToHand(card, hand){
    var container = document.getElementById(hand);
    var img = document.createElement("img");
    img.setAttribute("src", "../static/cards/" + card + ".svg");
    if (hand==='divHandSouth')
    {
        img.setAttribute("class", "pcard");
    }else{
        img.setAttribute("class", "pcard-small");
    }


    img.setAttribute("id", "card_" + card);
    img.onclick = function(){OnCardClick(card, hand);};
    container.appendChild(img);
}
function OnCardClick(theCard, hand){
    if (hand==='divHandSouth'){
        if (discardMode){
            discardMode = false;
            socket.emit('discard', theCard);
            $('#divMessage').html("");
        }
        else if (PlayableCards.includes(theCard)){
            socket.emit('play', theCard);
            PlayableCards = [];
            $('#divMessage').html("");
        }
    }
}


function SetPlayCard(card, elem, grayed){
    var container = document.getElementById(elem);
    container.innerHTML = "";
    if (card !== null){
        var img = document.createElement("img");
        img.setAttribute("src", "../static/cards/" + card + ".svg")
        if (grayed)
            img.setAttribute("class", "pcard-grayed")
        else
            img.setAttribute("class", "pcard")
        container.innerHTML = "";
        container.appendChild(img);
    }

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

