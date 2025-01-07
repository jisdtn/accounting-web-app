import axios from 'axios';

const state = {
  balances: null,
  balance: null
};

const getters = {
  stateBalances: state => state.balances,
  stateBalance: state => state.balance,
};

const actions = {
  async createBalance({dispatch}, balance) {
    await axios.post('balances', balance);
    await dispatch('getBalances');
  },
  async getBalances({commit}) {
    let {data} = await axios.get('balances');
    commit('setBalances', data);
  },
  async viewBalance({commit}, id) {
    let {data} = await axios.get(`balance/${id}`);
    commit('setBalance', data);
  },
  // eslint-disable-next-line no-empty-pattern
  async updateBalance({}, balance) {
    await axios.patch(`note/${balance.id}`, balance.form);
  },
  // eslint-disable-next-line no-empty-pattern
  async deleteNote({}, id) {
    await axios.delete(`note/${id}`);
  }
};

const mutations = {
  setBalances(state, balances){
    state.balances = balances;
  },
  setNote(state, note){
    state.note = note;
  },
};

export default {
  state,
  getters,
  actions,
  mutations
};
