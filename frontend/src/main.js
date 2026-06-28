window.onerror = function(m, s, l, c, e) { console.error('JS Error:', m, s, l, c); };
import { createApp } from 'vue';
import App from './App.vue';
import './index.css';

createApp(App).mount('#root');
