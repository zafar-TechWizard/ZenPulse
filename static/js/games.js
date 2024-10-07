document.addEventListener('DOMContentLoaded', () => {
    const gameBoard = document.querySelector('.game-board');
    const resetButton = document.getElementById('reset-game');
    let flippedCards = [];
    let matchedPairs = 0;

    gameBoard.addEventListener('click', flipCard);
    resetButton.addEventListener('click', resetGame);

    function flipCard(e) {
        const clickedCard = e.target.closest('.card');
        if (!clickedCard || clickedCard.classList.contains('flipped')) return;

        clickedCard.classList.add('flipped');
        flippedCards.push(clickedCard);

        if (flippedCards.length === 2) {
            gameBoard.removeEventListener('click', flipCard);
            checkForMatch();
        }
    }

    function checkForMatch() {
        const [card1, card2] = flippedCards;
        const card1Value = card1.dataset.card;
        const card2Value = card2.dataset.card;

        fetch('/check_match', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ card1: card1Value, card2: card2Value }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.match) {
                matchedPairs++;
                if (matchedPairs === 8) {
                    setTimeout(() => alert('Congratulations! You won!'), 500);
                }
            } else {
                setTimeout(() => {
                    card1.classList.remove('flipped');
                    card2.classList.remove('flipped');
                }, 1000);
            }
            flippedCards = [];
            gameBoard.addEventListener('click', flipCard);
        });
    }

    function resetGame() {
        location.reload();
    }
});
