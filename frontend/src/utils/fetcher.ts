import axios from 'axios';

export const fetcher = (url, config) =>
  axios.get(url, config).then((res) => res.data);
