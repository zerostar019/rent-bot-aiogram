export const fetcher = (url: URL) =>
  fetch(url).then((r) => {
    if (r.ok) {
      return r.json();
    }
    const err = new Error();
    err.message = "Something went wrong";
    throw err;
  });
