const mongoose = require('mongoose');

const assessmentSchema = new mongoose.Schema({
  assessmentID: {
    type: String,
    required: true,
    unique: true,
  },
//   instructions: {
//     type: String,
//     required: true,
//   },
});
const Assessment = mongoose.model('Assessment', assessmentSchema);
module.exports = Assessment;
