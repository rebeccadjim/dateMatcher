import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  vus: 10,
  duration: '30s',
  cloud: {
    // Project: Default project
    projectID: 3725101,
    // Test runs with the same name groups test runs together.
    name: 'Test (19/11/2024-22:27:37)'
  }
};

export default function() {
  http.get('https://test.k6.io');
  sleep(1);
}
