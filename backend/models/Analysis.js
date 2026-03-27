import mongoose from "mongoose";

const analysisSchema = new mongoose.Schema(
  {
    inputText: {
      type: String,
      required: true,
      trim: true,
    },
    method: {
      type: String,
      enum: ["lime", "shap"],
      required: true,
    },
    topK: {
      type: Number,
      required: true,
      min: 1,
      max: 50,
    },
    prediction: {
      type: mongoose.Schema.Types.Mixed,
      required: true,
    },
    explanation: {
      type: [mongoose.Schema.Types.Mixed],
      default: [],
    },
  },
  {
    timestamps: true,
  }
);

export const Analysis = mongoose.models.Analysis || mongoose.model("Analysis", analysisSchema);
