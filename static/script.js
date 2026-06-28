      // Horizontal Grid Scroll function
        function scrollGrid(gridId, direction) {
            const grid = document.getElementById(gridId);
            if (grid) {
                const scrollAmount = grid.clientWidth * 0.75;
                grid.scrollBy({
                    left: direction * scrollAmount,
                    behavior: 'smooth'
                });
            }
        }

        // Carousel logic
        document.addEventListener('DOMContentLoaded', () => {

            const carousel = document.getElementById('featuredCarousel');
            if (!carousel) return;

            const slides = Array.from(carousel.querySelectorAll('.carousel-slide'));
            const total = slides.length;
            if (total === 0) return;

            let currentIndex = 0;
            let slideInterval;

            const dotsContainer = document.getElementById('carouselDots');
            
            // Create pagination dots
            for (let i = 0; i < total; i++) {
                const dot = document.createElement('div');
                dot.className = `carousel-dot ${i === 0 ? 'active' : ''}`;
                dot.addEventListener('click', () => {
                    goToSlide(i);
                    resetTimer();
                });
                dotsContainer.appendChild(dot);
            }

            const dots = Array.from(dotsContainer.querySelectorAll('.carousel-dot'));

            function updateCarouselClasses() {
                slides.forEach((slide, index) => {
                    slide.className = 'carousel-slide'; // reset class
                    
                    if (index === currentIndex) {
                        slide.classList.add('active');
                    } else if (index === (currentIndex + 1) % total) {
                        slide.classList.add('right-card');
                    } else if (index === (currentIndex - 1 + total) % total) {
                        slide.classList.add('left-card');
                    }
                });

                dots.forEach((dot, index) => {
                    if (index === currentIndex) {
                        dot.classList.add('active');
                    } else {
                        dot.classList.remove('active');
                    }
                });
            }

            function goToSlide(index) {
                currentIndex = index;
                updateCarouselClasses();
            }

            function nextSlide() {
                currentIndex = (currentIndex + 1) % total;
                updateCarouselClasses();
            }

            function prevSlide() {
                currentIndex = (currentIndex - 1 + total) % total;
                updateCarouselClasses();
            }

            document.getElementById('carouselNext').addEventListener('click', () => {
                nextSlide();
                resetTimer();
            });

            document.getElementById('carouselPrev').addEventListener('click', () => {
                prevSlide();
                resetTimer();
            });

            function startTimer() {
                slideInterval = setInterval(nextSlide, 5000);
            }

            function resetTimer() {
                clearInterval(slideInterval);
                startTimer();
            }

            // Start auto slide
            startTimer();
            updateCarouselClasses();
            
        });
        
        //genre logic
        document.addEventListener('DOMContentLoaded', () => {

    const genreBoxes = document.querySelectorAll(
        'input[name="favorite_genres"], input[name="disliked_genres"]'
    );

    if (genreBoxes.length === 0) return;

    function updateGenreAvailability() {

        const liked = document.querySelectorAll(
            'input[name="favorite_genres"]'
        );

        const disliked = document.querySelectorAll(
            'input[name="disliked_genres"]'
        );

        liked.forEach(likeBox => {

            const value = likeBox.value;

            disliked.forEach(dislikeBox => {

                if (dislikeBox.value === value) {

                    const chip = document.querySelector(
                        `label[for="${dislikeBox.id}"]`
                    );

                    if (likeBox.checked) {

                        dislikeBox.disabled = true;
                        chip.classList.add('disabled-chip');

                    } else {

                        dislikeBox.disabled = false;
                        chip.classList.remove('disabled-chip');
                    }
                }
            });
        });

        disliked.forEach(dislikeBox => {

            const value = dislikeBox.value;

            liked.forEach(likeBox => {

                if (likeBox.value === value) {

                    const chip = document.querySelector(
                        `label[for="${likeBox.id}"]`
                    );

                    if (dislikeBox.checked) {

                        likeBox.disabled = true;
                        chip.classList.add('disabled-chip');

                    } else {

                        likeBox.disabled = false;
                        chip.classList.remove('disabled-chip');
                    }
                }
            });
        });
    }

    genreBoxes.forEach(box => {
        box.addEventListener('change', updateGenreAvailability);
    });

    updateGenreAvailability();

});
        