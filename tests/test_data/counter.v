`timescale 1ns/1ns

module counter (
    input           clock,
    input           reset,
    output  reg [3:0] count
);

    always @(posedge clock) begin
        if (reset) begin
            count <= 4'd0;
        end else begin
            count <= count + 1'b1;
        end
    end

endmodule

module tb_counter;

    reg         clock;
    reg         reset;
    wire [3:0]  count;

    counter u_counter (
        .clock  (clock  ),
        .reset  (reset  ),
        .count  (count  )
    );

    initial begin
        forever begin
            clock = 0; #5;
            clock = 1; #5;
        end
    end

    initial begin
        reset = 1;
        #10;
        reset = 0;
        #100;  // Let it count for 100ns
        $finish;
    end

    initial begin
        $dumpfile("counter.vcd");
        $dumpvars(0, tb_counter);
    end

endmodule
