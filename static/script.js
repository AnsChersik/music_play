document.addEventListener("DOMContentLoaded", () => {
  const loadMoreBtn = document.getElementById("load-more");
  const loading = document.getElementById("loading");
  const noMore = document.getElementById("no-more");
  const cardsGrid = document.getElementById("cards");

  if (loadMoreBtn) {
    loadMoreBtn.addEventListener("click", async () => {
      const page = loadMoreBtn.dataset.page;

      loading.style.display = "inline";
      loadMoreBtn.disabled = true;
      loadMoreBtn.textContent = "Загрузка...";

      try {
        const response = await fetch(`/api/films?page=${page}`);
        const data = await response.json();

        data.cards.forEach((card) => {
          const cardHTML = `
                    <div class="card" onclick="window.location.href='/film/${card.kinopoiskId}'">
                        <img class="card-poster" 
                             src="${card.poster}" 
                             alt="${card.title}"
                             onerror="this.src='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8z8AARAwMjDAGAP1wAgX8+/ePAAAAAElFTkSuQmCC'">
                        <div class="card-title">${card.title}</div>
                        <div class="card-genres">${card.genres}</div>
                        <div class="card-rating"> ${card.rating} ⭐</div>
                    </div>
                `;
          cardsGrid.insertAdjacentHTML("beforeend", cardHTML);
        });

        if (data.has_more) {
          loadMoreBtn.dataset.page = parseInt(page) + 1;
          loading.style.display = "none";
          loadMoreBtn.disabled = false;
          loadMoreBtn.textContent = "Показать ещё";
        } else {
          loadMoreBtn.style.display = "none";
          loading.style.display = "none";
          noMore.style.display = "block";
        }
      } catch (error) {
        console.error("Ошибка загрузки:", error);
        loading.style.display = "none";
        loadMoreBtn.disabled = false;
        loadMoreBtn.textContent = "Ошибка";
        alert("Не удалось загрузить фильмы.");
      }
    });
  }

  const favoritesBtn = document.querySelector(".favorites-btn");
  if (favoritesBtn) {
    const filmId = favoritesBtn.getAttribute("data-film-id");

    if (!filmId) {
      console.error("Film ID not found in data-film-id attribute");
      favoritesBtn.textContent = "ОШИБКА";
      return;
    }

    function updateButtonText(inFavorites) {
      if (inFavorites) {
        favoritesBtn.textContent = "УДАЛИТЬ ИЗ ИЗБРАННОГО";
        favoritesBtn.classList.add("active");
      } else {
        favoritesBtn.textContent = "ДОБАВИТЬ В ИЗБРАННОЕ";
        favoritesBtn.classList.remove("active");
      }
    }

    fetch(`/api/profile/check/${filmId}`)
      .then((r) => {
        return r.json();
      })
      .then((data) => {
        updateButtonText(data.in_favorites);
      })
      .catch((err) => {
        console.error("Ошибка проверки избранного:", err);
        favoritesBtn.textContent = "ДОБАВИТЬ В ИЗБРАННОЕ";
      });

    favoritesBtn.addEventListener("click", function () {
      favoritesBtn.disabled = true;
      const originalText = favoritesBtn.textContent;
      favoritesBtn.textContent = "...";

      fetch(`/api/profile/toggle/${filmId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      })
        .then((r) => {
          return r.json();
        })
        .then((data) => {
          if (data.success) {
            updateButtonText(data.in_favorites);
            alert(data.message);
          } else {
            alert("Ошибка: " + (data.message || "Неизвестная ошибка"));
            favoritesBtn.textContent = originalText;
          }
        })
        .catch((err) => {
          console.error("Ошибка:", err);
          alert(
            "Произошла ошибка при обновлении избранного. Проверьте консоль (F12).",
          );
          favoritesBtn.textContent = originalText;
        })
        .finally(() => {
          favoritesBtn.disabled = false;
        });
    });
  } 

  const removeButtons = document.querySelectorAll(".remove-btn");

  removeButtons.forEach((btn) => {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      const filmId = this.getAttribute("data-film-id");
      const card = this.closest(".favorite-card");

      if (!filmId) {
        alert("Ошибка: не найден ID фильма");
        return;
      }

      if (confirm("Вы уверены, что хотите удалить этот фильм из избранного?")) {
        fetch(`/api/profile/remove/${filmId}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        })
          .then((r) => {
            return r.json();
          })
          .then((data) => {
            if (data.success) {
              if (card) {
                card.style.transition = "opacity 0.3s, transform 0.3s";
                card.style.opacity = "0";
                card.style.transform = "scale(0.95)";
                setTimeout(() => {
                  card.remove();
                  if (
                    document.querySelectorAll(".favorite-card").length === 0
                  ) {
                    location.reload();
                  }
                }, 300);
              }
              alert("Фильм удалён из избранного");
            } else {
              alert("Ошибка: " + (data.message || "Неизвестная ошибка"));
            }
          })
          .catch((err) => {
            console.error("Ошибка:", err);
            alert("Ошибка");
          });
      }
    });
  });
});
