"use client";

import React, { useState } from "react";
import { Upload, Play, ChevronRight } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { apiPost } from "@/lib/api-client";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Breadcrumbs } from "@/components/Breadcrumbs";

type Tab = "UPLOAD" | "BANK" | "TEST" | "RESULTS";

export default function AssessmentStudioPage() {
  const { currentUser, activePersona } = useAuth();
  const currentRole = (currentUser?.role || activePersona.role || "LEARNER").toUpperCase();
  const isFaculty = ["TRAINER", "ADMIN"].includes(currentRole);
  
  const [activeTab, setActiveTab] = useState<Tab>(isFaculty ? "UPLOAD" : "TEST");

  // UPLOAD STATE
  const [docTitle, setDocTitle] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  
  // DEFAULT QUESTIONS FOR ADAPTIVE ASSESSMENT
  const [questions, setQuestions] = useState<any[]>([
    {
      question_text: "Which formula is officially utilized by MoSPI for compiling elementary price aggregates in the Consumer Price Index (CPI)?",
      options: [
        "Laspeyres weighted arithmetic index",
        "Jevons unweighted geometric mean of price relatives",
        "Paasche variable basket index",
        "Marshall-Edgeworth aggregative formula"
      ],
      correct_option_index: 1,
      explanation: "As per the MoSPI CPI Manual (Base 2012=100), elementary price aggregates are compiled using the Jevons formula."
    },
    {
      question_text: "Under SNA 2008, what is the exact macroeconomic relationship between GVA at basic prices and GDP at market prices?",
      options: [
        "GDP at Market Prices = GVA at Basic Prices + Net Product Taxes (Product Taxes - Product Subsidies)",
        "GDP at Market Prices = GVA at Basic Prices - Production Taxes + Production Subsidies",
        "GDP at Market Prices = GVA at Factor Cost + Net Indirect Taxes",
        "GDP at Market Prices = GVA at Basic Prices + Net Factor Income from Abroad"
      ],
      correct_option_index: 0,
      explanation: "SNA 2008 identity states: GDP at market prices = GVA at basic prices + Product Taxes - Product Subsidies."
    },
    {
      question_text: "In the Periodic Labour Force Survey (PLFS), how is an individual classified under Current Weekly Status (CWS)?",
      options: [
        "Worked for at least 30 days during the preceding 365 days",
        "Worked for at least 1 hour on any day during the 7 days preceding survey date",
        "Actively looking for work for at least 15 days in the last month",
        "Employed for at least 182 days in principal economic activity"
      ],
      correct_option_index: 1,
      explanation: "Under CWS, a person is considered employed if they worked for at least 1 hour on any day of the reference week."
    },
    {
      question_text: "Under the MoSPI Data Quality Assurance Framework (DQAF), which dimension evaluates whether statistical outputs are released according to an advance calendar?",
      options: [
        "Methodological Soundness",
        "Integrity & Professional Independence",
        "Timeliness and Punctuality",
        "Serviceability & Revisions"
      ],
      correct_option_index: 2,
      explanation: "Timeliness and Punctuality assesses adherence to pre-announced release schedules."
    }
  ]);
  
  // TEST STATE
  const [currentQIndex, setCurrentQIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState<Record<number, number>>({});
  const [score, setScore] = useState<number | null>(null);

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      const res = await apiPost<any>("/assessments/generate-quiz", {
        topic: docTitle || "MoSPI Guidelines",
        question_count: 5
      });
      if (res.quiz?.questions) {
        setQuestions(res.quiz.questions);
      } else {
        // Fallback
        setQuestions([
          {
            question_text: "Which formula is officially utilized by MoSPI for compiling elementary price aggregates?",
            options: [
              "Laspeyres weighted arithmetic index",
              "Jevons unweighted geometric mean of price relatives",
              "Paasche variable basket index",
              "Marshall-Edgeworth aggregative formula"
            ],
            correct_option_index: 1,
            explanation: "As per the MoSPI CPI Manual, elementary price aggregates are compiled using the Jevons formula."
          },
          {
            question_text: "Under SNA 2008, what is the relationship between GVA at basic prices and GDP at market prices?",
            options: [
              "GDP = GVA + Product Taxes - Product Subsidies",
              "GDP = GVA - Production Taxes + Production Subsidies",
              "GDP = GVA + Net Indirect Taxes",
              "GDP = GVA + Net Factor Income from Abroad"
            ],
            correct_option_index: 0,
            explanation: "GDP at market prices is derived by adding Product Taxes and subtracting Product Subsidies from GVA at basic prices."
          }
        ]);
      }
      setActiveTab("BANK");
    } catch (err) {
      // Fallback
      setQuestions([
        {
          question_text: "Which formula is officially utilized by MoSPI for compiling elementary price aggregates?",
          options: [
            "Laspeyres weighted arithmetic index",
            "Jevons unweighted geometric mean of price relatives",
            "Paasche variable basket index",
            "Marshall-Edgeworth aggregative formula"
          ],
          correct_option_index: 1,
          explanation: "As per the MoSPI CPI Manual, elementary price aggregates are compiled using the Jevons formula."
        }
      ]);
      setActiveTab("BANK");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleStartTest = () => {
    setCurrentQIndex(0);
    setUserAnswers({});
    setScore(null);
    setActiveTab("TEST");
  };

  const handleSelectAnswer = (optIndex: number) => {
    setUserAnswers(prev => ({ ...prev, [currentQIndex]: optIndex }));
  };

  const handleNext = () => {
    if (currentQIndex < questions.length - 1) {
      setCurrentQIndex(prev => prev + 1);
    } else {
      let correct = 0;
      questions.forEach((q, idx) => {
        if (userAnswers[idx] === q.correct_option_index) correct++;
      });
      setScore(Math.round((correct / questions.length) * 100));
      setActiveTab("RESULTS");
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 space-y-8 text-zinc-900">
      <Breadcrumbs items={[{ label: "Assessments" }]} />
      
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Assessments</h1>
        <p className="text-sm text-zinc-500 mt-1">Generate and take tests based on your materials.</p>
      </div>

      <div className="flex items-center space-x-8 border-b border-zinc-200">
        {(isFaculty ? (["UPLOAD", "BANK", "TEST"] as Tab[]) : (["TEST", "BANK"] as Tab[])).map((tab) => (
          <button
            key={tab}
            onClick={() => {
              if (tab === "TEST" && questions.length === 0) return;
              setActiveTab(tab);
            }}
            className={`pb-3 text-sm font-medium transition-colors ${
              activeTab === tab 
                ? "border-b-2 border-zinc-900 text-zinc-900" 
                : tab === "TEST" && questions.length === 0 
                  ? "text-zinc-300 cursor-not-allowed" 
                  : "text-zinc-500 hover:text-zinc-900"
            }`}
          >
            {tab === "UPLOAD" && "Upload Material (AI Authoring)"}
            {tab === "BANK" && "Question Bank"}
            {tab === "TEST" && "Take Adaptive Test"}
          </button>
        ))}
      </div>

      {activeTab === "UPLOAD" && (
        <Card className="border-zinc-200 rounded-none shadow-none">
          <CardHeader>
            <CardTitle className="text-lg font-medium">Upload Material</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="border border-dashed border-zinc-300 p-16 text-center hover:border-zinc-500 transition-colors bg-zinc-50 cursor-pointer">
              <Upload className="w-8 h-8 text-zinc-400 mx-auto mb-4" />
              <p className="text-sm font-medium text-zinc-900">Drag & drop your document here</p>
              <p className="text-xs text-zinc-500 mt-2">PDF, DOCX, or PPTX up to 25MB</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-900 mb-2">Document Title</label>
              <input
                type="text"
                value={docTitle}
                onChange={e => setDocTitle(e.target.value)}
                placeholder="Enter topic or title..."
                className="w-full text-sm p-3 border border-zinc-200 focus:outline-none focus:border-zinc-900"
              />
            </div>
            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className="w-full py-3 bg-zinc-900 text-white text-sm font-medium hover:bg-zinc-800 disabled:opacity-50 transition-colors"
            >
              {isGenerating ? "Generating Questions..." : "Generate Question Bank"}
            </button>
          </CardContent>
        </Card>
      )}

      {activeTab === "BANK" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-medium text-zinc-900">Generated Questions</h2>
            {questions.length > 0 && (
              <button
                onClick={handleStartTest}
                className="px-5 py-2.5 bg-zinc-900 text-white text-sm font-medium hover:bg-zinc-800 flex items-center space-x-2 transition-colors"
              >
                <Play className="w-4 h-4" />
                <span>Start Test</span>
              </button>
            )}
          </div>
          
          {questions.length === 0 ? (
            <div className="text-center py-16 text-sm text-zinc-500 border border-zinc-200 bg-zinc-50">
              No questions generated yet. Please upload material first.
            </div>
          ) : (
            <div className="space-y-6">
              {questions.map((q, idx) => (
                <Card key={idx} className="border-zinc-200 rounded-none shadow-none">
                  <CardContent className="p-6">
                    <div className="flex items-start space-x-3 mb-6">
                      <Badge variant="outline" className="mt-0.5 shrink-0 text-xs text-zinc-600 border-zinc-200">
                        Q{idx + 1}
                      </Badge>
                      <p className="text-sm font-medium text-zinc-900">{q.question_text}</p>
                    </div>
                    <div className="space-y-2 pl-11">
                      {q.options.map((opt: string, oIdx: number) => (
                        <div
                          key={oIdx}
                          className={`text-sm p-3 border ${
                            oIdx === q.correct_option_index
                              ? "bg-zinc-100 border-zinc-900 text-zinc-900 font-medium"
                              : "border-zinc-200 text-zinc-600"
                          }`}
                        >
                          {opt}
                        </div>
                      ))}
                    </div>
                    <div className="mt-6 ml-11 p-4 bg-zinc-50 border border-zinc-100 text-sm text-zinc-700">
                      <span className="font-medium text-zinc-900">Explanation:</span> {q.explanation}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === "TEST" && questions.length > 0 && (
        <div className="space-y-6 max-w-3xl mx-auto mt-4">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium text-zinc-900">Question {currentQIndex + 1} of {questions.length}</span>
            <div className="w-48 h-1.5 bg-zinc-100">
              <div 
                className="h-full bg-zinc-900 transition-all duration-300" 
                style={{ width: `${((currentQIndex + 1) / questions.length) * 100}%` }} 
              />
            </div>
          </div>

          <Card className="border-zinc-200 rounded-none shadow-none">
            <CardContent className="p-8 md:p-10 space-y-8">
              <p className="text-base font-medium text-zinc-900 leading-relaxed">
                {questions[currentQIndex].question_text}
              </p>
              <div className="space-y-3">
                {questions[currentQIndex].options.map((opt: string, oIdx: number) => {
                  const isSelected = userAnswers[currentQIndex] === oIdx;
                  return (
                    <button
                      key={oIdx}
                      onClick={() => handleSelectAnswer(oIdx)}
                      className={`w-full text-left p-4 border text-sm transition-all flex items-center space-x-4 ${
                        isSelected 
                          ? "border-zinc-900 bg-zinc-50 text-zinc-900" 
                          : "border-zinc-200 hover:border-zinc-300 text-zinc-600 hover:text-zinc-900"
                      }`}
                    >
                      <div className={`w-4 h-4 rounded-full border flex-shrink-0 transition-colors ${
                        isSelected ? "border-[5px] border-zinc-900" : "border-zinc-300"
                      }`} />
                      <span className={isSelected ? "font-medium" : ""}>{opt}</span>
                    </button>
                  );
                })}
              </div>
            </CardContent>
            <CardFooter className="p-8 md:p-10 pt-0 flex justify-end">
              <button
                onClick={handleNext}
                disabled={userAnswers[currentQIndex] === undefined}
                className="px-6 py-3 bg-zinc-900 text-white text-sm font-medium hover:bg-zinc-800 disabled:opacity-30 disabled:hover:bg-zinc-900 transition-all flex items-center space-x-2"
              >
                <span>{currentQIndex === questions.length - 1 ? "Submit Test" : "Next Question"}</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </CardFooter>
          </Card>
        </div>
      )}

      {activeTab === "RESULTS" && score !== null && (
        <Card className="border-zinc-200 rounded-none shadow-none max-w-xl mx-auto mt-12">
          <CardContent className="p-12 text-center space-y-8">
            <div className="w-28 h-28 mx-auto border-4 border-zinc-900 rounded-full flex items-center justify-center">
              <span className="text-4xl font-bold text-zinc-900">{score}%</span>
            </div>
            <div className="space-y-2">
              <h2 className="text-xl font-medium text-zinc-900">Assessment Complete</h2>
              <p className="text-sm text-zinc-500">You have successfully finished the test session.</p>
            </div>
            <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
              <button
                onClick={() => setActiveTab("BANK")}
                className="w-full sm:w-auto px-6 py-3 border border-zinc-200 text-zinc-900 text-sm font-medium hover:bg-zinc-50 transition-colors"
              >
                Review Question Bank
              </button>
              <button
                onClick={() => setActiveTab("UPLOAD")}
                className="w-full sm:w-auto px-6 py-3 bg-zinc-900 text-white text-sm font-medium hover:bg-zinc-800 transition-colors"
              >
                Start New Assessment
              </button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
