document.addEventListener("DOMContentLoaded", () => {
  const loadMoreBtn = document.getElementById("load-more");
  const loading = document.getElementById("loading");
  const noMore = document.getElementById("no-more");
  const cardsGrid = document.getElementById("cards");

  if (!loadMoreBtn) {
    console.log('Кнопка "Показать ещё" не найдена');
    return;
  }

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
                    <div class="card">
                        <img class="card-poster" 
                             src="${card.poster}" 
                             alt="${card.title}"
                             onerror="this.src='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8z8AARAwMjDAGAP1wAgX8+/ePAAAAAElFTkSuQmCC'">
                        <div class="card-title">${card.title}</div>
                        <div class="card-genres">${card.genres}</div>
                        <div class="card-rating"> ${card.rating}</div>
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
});
