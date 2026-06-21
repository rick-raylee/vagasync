const fs = require('fs');

let content = fs.readFileSync('frontend/src/App.vue', 'utf8');

const old_table = `<tr v-for="i in 6" :key="i">
                      <td>#{{ 1024 + i }}</td>
                      <td style="font-weight: 600;">usuario{{ i }}@vagasync.com.br</td>
                      <td>
                        <span style="font-size: 0.75rem; padding: 2px 7px; border-radius: 4px; background: rgba(59,130,246,0.15); color: #60a5fa; font-weight: 600;">
                          {{ i % 2 === 0 ? 'Recruiter Pro' : 'Candidate Premium' }}
                        </span>
                      </td>
                      <td>
                        <span style="font-size: 0.75rem; text-transform: uppercase; color: var(--text-secondary);">
                          {{ i % 3 === 0 ? 'Stripe' : i % 3 === 1 ? 'MercadoPago' : 'Pix' }}
                        </span>
                      </td>
                      <td style="font-weight: 700; color: #fff;">
                        R$ {{ i % 2 === 0 ? '149,90' : '29,90' }}
                      </td>
                      <td>
                        <span style="font-size: 0.7rem; padding: 2px 6px; border-radius: 12px; font-weight: 700; background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.3); color: var(--color-success);">
                          PAGO
                        </span>
                      </td>
                    </tr>`;

const new_table = `<tr v-for="i in 6" :key="i">
                      <td>#{{ 1024 + i }}</td>
                      <td style="font-weight: 600;">usuario{{ i }}@vagasync.com.br</td>
                      <td>
                        <span style="font-size: 0.75rem; padding: 2px 7px; border-radius: 4px; background: rgba(59,130,246,0.15); color: #60a5fa; font-weight: 600;">
                          {{ i === 1 ? 'IA Avançada Triagem' : i === 2 ? 'IA Ilimitada' : i === 3 ? 'Empresa Destaque' : i === 4 ? 'Perfil Premium' : i === 5 ? 'Videoentrevistas' : 'Impulsionar Vaga' }}
                        </span>
                      </td>
                      <td>
                        <span style="font-size: 0.75rem; text-transform: uppercase; color: var(--text-secondary);">
                          {{ i % 3 === 0 ? 'Stripe' : i % 3 === 1 ? 'MercadoPago' : 'Pix' }}
                        </span>
                      </td>
                      <td style="font-weight: 700; color: #fff;">
                        R$ {{ i === 1 ? '9,90' : i === 2 ? '7,90' : i === 3 ? '4,99' : i === 4 ? '4,99' : i === 5 ? '4,99' : '2,99' }}
                      </td>
                      <td>
                        <span style="font-size: 0.7rem; padding: 2px 6px; border-radius: 12px; font-weight: 700; background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.3); color: var(--color-success);">
                          PAGO
                        </span>
                      </td>
                    </tr>`;

content = content.split(old_table).join(new_table);

fs.writeFileSync('frontend/src/App.vue', content, 'utf8');
console.log("Admin table refactored!");
