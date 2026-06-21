window.onerror = function(m, s, l, c, e) { alert('JS Error: ' + m); };
import { createApp } from 'vue';
import App from './App.vue';
import './index.css';

createApp(App).mount('#root');
