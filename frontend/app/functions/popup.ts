export function setPopup(baseUrl: string, id: number, name: string) {
  const url = `#/${baseUrl}/${id}/`;

  const popup = `
    <div>
      <h4>${name}</h4>
      <a href="${url}">
          <i class="fa fa-eye" aria-hidden="true"></i>
        </a>
    </div>
    `;

  return popup;
}
