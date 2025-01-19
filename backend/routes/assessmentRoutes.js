const express = require('express');
const router = express.Router();
const Assessment = require('../models/Assessment');

// POST route to validate Assessment ID
router.post('/api/validate-assessment', async (req, res) => {
  const { assessmentId } = req.body;

  try {
    const assessment = await Assessment.findOne({ assessmentID : assessmentId});
    if (assessment) {
    //   return res.json({
    //     success: true,
    //     instructions: assessment.instructions,

      //});
      return res.status(200).json({ message: 'Valid Assessment ID' });
    } else {
        return res.status(400).json({ message: 'Invalid Assessment ID' });
    }
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: 'Server error' });
  }
});

module.exports = router;
