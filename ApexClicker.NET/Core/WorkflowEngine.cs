using System;
using System.Collections.ObjectModel;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace ApexClicker.Core
{
    public enum StepType
    {
        TemplateSearch,
        PixelCheck,
        ClickCoordinate,
        MultiPointSequence,
        KeyPress,
        Delay
    }

    public class WorkflowStep
    {
        public int Id { get; set; }
        public string Title { get; set; } = "New Step";
        public StepType Type { get; set; } = StepType.ClickCoordinate;
        public bool IsEnabled { get; set; } = true;

        // Details / Parameters
        public int TargetX { get; set; }
        public int TargetY { get; set; }
        public int RegionX { get; set; }
        public int RegionY { get; set; }
        public int RegionWidth { get; set; }
        public int RegionHeight { get; set; }
        public string TemplateFile { get; set; } = "";
        public string TargetKey { get; set; } = "Enter";
        public int DelayMs { get; set; } = 500;

        // Branching logic
        public int OnSuccessJump { get; set; } = 0; // 0 = Next step
        public int OnFailJump { get; set; } = 0;    // 0 = Stop, -1 = Skip, >0 = Step ID

        [JsonIgnore]
        public string TypeBadge => Type switch
        {
            StepType.TemplateSearch => "🖼️ Visual Bot",
            StepType.PixelCheck => "👁️ Pixel Check",
            StepType.ClickCoordinate => "🎯 Click Point",
            StepType.MultiPointSequence => "📍 Sequence",
            StepType.KeyPress => "⌨️ Key Press",
            StepType.Delay => "⏱️ Wait Delay",
            _ => "⚙️ Action"
        };

        [JsonIgnore]
        public string SummaryDescription => Type switch
        {
            StepType.TemplateSearch => $"Search '{TemplateFile}' in Region ({RegionX},{RegionY} {RegionWidth}x{RegionHeight}) -> Click found target",
            StepType.PixelCheck => $"Wait until pixel ({TargetX},{TargetY}) matches target color",
            StepType.ClickCoordinate => $"Click at screen ({TargetX}, {TargetY})",
            StepType.MultiPointSequence => $"Execute sequence path across assigned points",
            StepType.KeyPress => $"Press key '{TargetKey}'",
            StepType.Delay => $"Pause for {DelayMs} ms",
            _ => "Custom action"
        };
    }

    public class WorkflowPipeline
    {
        public string Name { get; set; } = "Default Workflow";
        public ObservableCollection<WorkflowStep> Steps { get; set; } = new();

        public static WorkflowPipeline CreateDemoPipeline()
        {
            var pipeline = new WorkflowPipeline { Name = "Full Automation Pipeline v2.0 Demo" };

            pipeline.Steps.Add(new WorkflowStep
            {
                Id = 1,
                Title = "Scan for Play Button in Region",
                Type = StepType.TemplateSearch,
                TemplateFile = "Play_Button.png",
                RegionX = 200,
                RegionY = 150,
                RegionWidth = 400,
                RegionHeight = 300,
                IsEnabled = true
            });

            pipeline.Steps.Add(new WorkflowStep
            {
                Id = 2,
                Title = "Human Wait Before Interaction",
                Type = StepType.Delay,
                DelayMs = 450,
                IsEnabled = true
            });

            pipeline.Steps.Add(new WorkflowStep
            {
                Id = 3,
                Title = "Verify Green Ready Pixel",
                Type = StepType.PixelCheck,
                TargetX = 960,
                TargetY = 540,
                IsEnabled = true
            });

            pipeline.Steps.Add(new WorkflowStep
            {
                Id = 4,
                Title = "Click Target Coordinate",
                Type = StepType.ClickCoordinate,
                TargetX = 850,
                TargetY = 620,
                IsEnabled = true
            });

            pipeline.Steps.Add(new WorkflowStep
            {
                Id = 5,
                Title = "Confirm Action",
                Type = StepType.KeyPress,
                TargetKey = "Enter",
                IsEnabled = true
            });

            return pipeline;
        }

        public string ToJson()
        {
            return JsonSerializer.Serialize(this, new JsonSerializerOptions { WriteIndented = true });
        }

        public static WorkflowPipeline? FromJson(string json)
        {
            return JsonSerializer.Deserialize<WorkflowPipeline>(json);
        }
    }
}
